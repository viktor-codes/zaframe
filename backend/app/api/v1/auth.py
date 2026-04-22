"""Authentication API router.

Magic link flow (strict cookie mode):
1. POST /auth/magic-link/request {email, name}
2. GET /auth/magic-link/verify?token=xxx -> returns access token JSON + sets refresh token httpOnly cookie
3. POST /auth/refresh -> reads refresh token from cookie, returns new access token JSON + rotates refresh cookie
4. POST /auth/logout -> revokes current refresh token (from cookie) and clears the cookie
"""

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import get_current_user_required, get_uow
from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.schemas.auth import (
    MagicLinkRequest,
    MagicLinkSentResponse,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth import (
    logout_current_session,
    refresh_access_token,
    request_magic_link,
    verify_magic_link,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def _set_csrf_cookie(response: Response, csrf_token: str) -> None:
    """
    Double-submit CSRF token cookie.

    - Not httpOnly: must be readable by JS to send X-CSRF-Token.
    - SameSite=Lax: helps mitigate CSRF for top-level navigations.
    - Paired with header check on sensitive cookie-auth endpoints (/refresh).
    """
    max_age_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=max_age_seconds,
        path="/",
    )


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
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


@router.post("/magic-link/request", response_model=MagicLinkSentResponse)
@limiter.limit("5/minute")
async def magic_link_request(
    request: Request,
    schema: MagicLinkRequest,
    uow: UnitOfWork = Depends(get_uow),
) -> MagicLinkSentResponse:
    """
    Request a magic link email.

    Creates the user on first request. Sends the email (or logs in dev).
    """
    await request_magic_link(uow, schema.email, schema.name)
    return MagicLinkSentResponse()


@router.get("/magic-link/verify")
@limiter.limit("10/minute")
async def magic_link_verify(
    request: Request,
    response: Response,
    token: str = Query(..., description="Token from the email link"),
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Verify magic link token and issue JWTs.

    Called when the user follows the email link. The frontend reads `token`
    from the query string and calls this endpoint.
    """
    user, access_token, refresh_token, csrf_token = await verify_magic_link(uow, token)
    _set_refresh_cookie(response, refresh_token)
    _set_csrf_cookie(response, csrf_token)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_tokens(
    request: Request,
    response: Response,
    uow: UnitOfWork = Depends(get_uow),
) -> TokenResponse:
    """Refresh access token using refresh token cookie."""
    _require_csrf_header(request)
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        from app.core.exceptions import UnauthorizedError

        raise UnauthorizedError("Missing refresh token cookie")

    access_token, new_refresh_token, new_csrf_token = await refresh_access_token(
        uow, refresh_token
    )
    _set_refresh_cookie(response, new_refresh_token)
    _set_csrf_cookie(response, new_csrf_token)
    return TokenResponse(
        access_token=access_token,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
) -> None:
    """
    Sign out of the current session.

    Revokes the refresh session from the cookie and clears the cookie.
    """
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    _clear_refresh_cookie(response)
    if refresh_token:
        await logout_current_session(uow, user, refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_me(
    user: User = Depends(get_current_user_required),
) -> UserResponse:
    """
    Return the current user from the Bearer access token.

    Protected endpoint — requires `Authorization: Bearer <access_token>`.
    """
    return user
