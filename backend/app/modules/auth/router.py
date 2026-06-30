from typing import Annotated

"""Authentication API router.

Email OTP flow (strict cookie mode):
1. POST /auth/otp/request {email, name}
2. POST /auth/otp/verify {email, code} -> access token JSON + refresh httpOnly cookie
3. POST /auth/refresh -> reads refresh token from cookie, rotates session
4. POST /auth/logout -> revokes current refresh token and clears cookies
"""

from fastapi import APIRouter, Depends, Request, Response

from app.core.config import settings
from app.core.deps import get_current_user_required, get_uow
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.auth.schemas import (
    CurrentUserResponse,
    OTPRequest,
    OTPSentResponse,
    OTPVerify,
    OTPVerifyResponse,
    TokenResponse,
)
from app.modules.auth.service import (
    logout_current_session,
    refresh_access_token,
    request_otp,
    verify_otp,
)
from app.modules.catalog.studio import get_current_user_studio_roles
from app.modules.identity import UserResponse
from app.modules.identity.schemas import CurrentUserUpdate
from app.modules.identity.service import (
    soft_delete_current_user_account,
    update_current_user_profile,
)

router = APIRouter(prefix="/auth", tags=["auth"])
account_router = APIRouter(prefix="/me", tags=["auth"])

REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def _set_csrf_cookie(response: Response, csrf_token: str) -> None:
    max_age_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=max_age_seconds,
        path="/",
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=max_age_seconds,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path="/",
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
    )


def _require_csrf_header(request: Request) -> None:
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise ForbiddenError("CSRF validation failed")


@router.post("/otp/request", response_model=OTPSentResponse)
@limiter.limit("10/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def otp_request(
    request: Request,
    schema: OTPRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OTPSentResponse:
    """Send a one-time sign-in code to email."""
    await request_otp(
        uow,
        schema.email,
        schema.name,
        request_ip=_client_ip(request),
    )
    return OTPSentResponse()


@router.post("/otp/verify", response_model=OTPVerifyResponse)
@limiter.limit("20/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def otp_verify(
    request: Request,
    response: Response,
    schema: OTPVerify,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OTPVerifyResponse:
    """Verify OTP code and issue JWT session."""
    user, access_token, refresh_token, csrf_token = await verify_otp(
        uow,
        schema.email,
        schema.code,
        booking_id=schema.booking_id,
    )
    _set_refresh_cookie(response, refresh_token)
    _set_csrf_cookie(response, csrf_token)
    return OTPVerifyResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def refresh_tokens(
    request: Request,
    response: Response,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> TokenResponse:
    """Refresh access token using refresh token cookie."""
    _require_csrf_header(request)
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise UnauthorizedError("Missing refresh token cookie")

    access_token, new_refresh_token, new_csrf_token = await refresh_access_token(uow, refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    _set_csrf_cookie(response, new_csrf_token)
    return TokenResponse(
        access_token=access_token,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> None:
    """Sign out of the current session."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    _clear_refresh_cookie(response)
    if refresh_token:
        await logout_current_session(uow, user, refresh_token)


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_me(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> CurrentUserResponse:
    """Return the current user from the Bearer access token."""
    return CurrentUserResponse(
        **UserResponse.model_validate(user).model_dump(),
        roles=await get_current_user_studio_roles(uow, user_id=user.id),
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user_me(
    schema: CurrentUserUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> UserResponse:
    """Update the current user's editable profile fields."""
    updated_user = await update_current_user_profile(uow, user, schema)
    return UserResponse.model_validate(updated_user)


@account_router.post("/delete-account", status_code=204)
async def delete_current_user_account(
    response: Response,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Soft-delete the current account and clear browser auth cookies."""
    _clear_refresh_cookie(response)
    await soft_delete_current_user_account(uow, user)
