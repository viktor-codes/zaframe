"""
Authentication business logic: email OTP and JWT sessions.
"""

from datetime import datetime, timedelta

import structlog

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.core.exceptions import ServiceUnavailableError, UnauthorizedError, ValidationError
from app.core.observability import log_domain_event
from app.core.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    generate_otp_code,
    get_otp_expires_at,
    get_user_id_from_access_token,
    hash_otp_code,
    parse_refresh_token,
    verify_otp_code,
)
from app.core.uow import UnitOfWork
from app.integrations.email import send_otp_email
from app.models.otp_code import OTPCode
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.modules.booking import attach_guest_resources
from app.modules.identity import get_or_create_user, get_user_by_id

_INVALID_OTP_MESSAGE = "Verification code is invalid or has expired"
_RATE_LIMIT_MESSAGE = "Too many verification codes requested. Try again later."
_OTP_DELIVERY_UNAVAILABLE_MESSAGE = "Verification email could not be sent. Please try again later."
logger = structlog.get_logger(__name__)


async def request_otp(
    uow: UnitOfWork,
    email: str,
    name: str,
    *,
    request_ip: str | None = None,
) -> None:
    """
    Generate and email an OTP.

    Does not create a User — registration happens on successful verify.
    """
    now_utc = utc_now()
    existing_user = await uow.users.get_by_email_including_deleted(email)

    since = now_utc - timedelta(hours=1)
    recent_count = await uow.otp_codes.count_recent_requests(email, since)
    if recent_count >= settings.OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR:
        log_domain_event(
            logger,
            "otp_request_rate_limited",
            level="warning",
            recent_count=recent_count,
        )
        raise ValidationError(_RATE_LIMIT_MESSAGE)

    await uow.otp_codes.invalidate_active_for_email(email, now_utc)

    code = generate_otp_code()
    await uow.otp_codes.add(
        OTPCode(
            email=email,
            code_hash=hash_otp_code(code),
            name=name,
            expires_at=get_otp_expires_at(),
            attempts=0,
            request_ip=request_ip,
        )
    )
    email_sent = await send_otp_email(email, code)
    if not email_sent:
        log_domain_event(
            logger,
            "otp_delivery_unavailable",
            level="error",
            user_id=existing_user.id if existing_user is not None else None,
        )
        raise ServiceUnavailableError(_OTP_DELIVERY_UNAVAILABLE_MESSAGE)

    log_domain_event(
        logger,
        "otp_requested",
        user_id=existing_user.id if existing_user is not None else None,
        delivery_accepted=email_sent,
    )


async def verify_otp(
    uow: UnitOfWork,
    email: str,
    code: str,
    *,
    booking_id: int | None = None,
) -> tuple[User, str, str, str]:
    """
    Verify OTP and issue JWT session tokens.

    Returns (user, access_token, refresh_token, csrf_token).
    """
    now_utc = utc_now()
    otp = await uow.otp_codes.get_latest_active_for_email(email, now_utc)
    if otp is None:
        log_domain_event(logger, "otp_verify_failed", level="warning", reason="missing_active_otp")
        raise ValidationError(_INVALID_OTP_MESSAGE)

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        otp.used_at = now_utc
        await uow.otp_codes.save(otp)
        log_domain_event(logger, "otp_verify_failed", level="warning", reason="max_attempts")
        raise ValidationError(_INVALID_OTP_MESSAGE)

    if not verify_otp_code(code, otp.code_hash):
        otp.attempts += 1
        if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            otp.used_at = now_utc
        await uow.otp_codes.save(otp)
        log_domain_event(
            logger,
            "otp_verify_failed",
            level="warning",
            reason="invalid_code",
            attempts=otp.attempts,
        )
        raise ValidationError(_INVALID_OTP_MESSAGE)

    return await _complete_otp_login(
        uow,
        otp,
        now_utc=now_utc,
        booking_id=booking_id,
    )


async def _complete_otp_login(
    uow: UnitOfWork,
    otp: OTPCode,
    *,
    now_utc: datetime,
    booking_id: int | None = None,
) -> tuple[User, str, str, str]:
    otp.used_at = now_utc
    await uow.otp_codes.save(otp)

    # WHY: name from OTP is registration-only; existing profiles are not overwritten on login.
    user = await get_or_create_user(uow, email=otp.email, name=otp.name)
    user.last_login_at = now_utc
    user = await uow.users.save(user)

    await attach_guest_resources(uow, user, booking_id=booking_id)
    log_domain_event(
        logger,
        "otp_verified",
        user_id=user.id,
        booking_id=booking_id,
    )

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    csrf_token = create_csrf_token()

    refresh_data = parse_refresh_token(refresh_token)
    if refresh_data is not None:
        await uow.refresh_tokens.add(
            RefreshToken(
                user_id=user.id,
                jti=refresh_data.jti,
                expires_at=refresh_data.expires_at,
            )
        )

    return user, access_token, refresh_token, csrf_token


async def refresh_access_token(
    uow: UnitOfWork,
    refresh_token: str,
) -> tuple[str, str, str]:
    """
    Issue new access token from refresh token.

    Returns (access_token, refresh_token, csrf_token).
    Raises UnauthorizedError if refresh token is invalid.
    """
    refresh_data = parse_refresh_token(refresh_token)
    if refresh_data is None:
        raise UnauthorizedError("Invalid refresh token")

    user_id = refresh_data.user_id
    jti = refresh_data.jti
    now_utc = utc_now()

    refresh_session = await uow.refresh_tokens.get_by_user_and_jti(user_id, jti)
    if refresh_session is None:
        raise UnauthorizedError("Invalid refresh token")
    if refresh_session.revoked_at is not None:
        revoked_count = await uow.refresh_tokens.revoke_active_for_user(user_id, now_utc)
        log_domain_event(
            logger,
            "refresh_token_reuse_detected",
            level="warning",
            user_id=user_id,
            revoked_sessions=revoked_count,
        )
        # WHY: this security side effect must survive the 401 response rollback path.
        await uow.commit()
        raise UnauthorizedError("Invalid refresh token")
    if not refresh_session.is_active(now_utc):
        raise UnauthorizedError("Invalid refresh token")

    refresh_session.revoked_at = now_utc
    refresh_session.last_used_at = now_utc

    user = await get_user_by_id(uow, user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)
    new_csrf_token = create_csrf_token()

    new_data = parse_refresh_token(new_refresh_token)
    if new_data is not None:
        await uow.refresh_tokens.add(
            RefreshToken(
                user_id=user.id,
                jti=new_data.jti,
                expires_at=new_data.expires_at,
            )
        )

    await uow.refresh_tokens.flush()
    return access_token, new_refresh_token, new_csrf_token


async def get_current_user_from_token(
    uow: UnitOfWork,
    token: str,
) -> User | None:
    """Resolve user from access token."""
    user_id = get_user_id_from_access_token(token)
    if user_id is None:
        return None
    return await get_user_by_id(uow, user_id)


async def logout_current_session(
    uow: UnitOfWork,
    user: User,
    refresh_token: str,
) -> None:
    """
    Sign out of current session (revoke one refresh token).

    If token is invalid or not owned by user — silent no-op (idempotent).
    If session exists and active — sets revoked_at / last_used_at.
    """
    data = parse_refresh_token(refresh_token)
    if data is None or data.user_id != user.id:
        return

    now_utc = utc_now()
    refresh_session = await uow.refresh_tokens.get_by_user_and_jti(user.id, data.jti)
    if refresh_session is None:
        return

    if refresh_session.revoked_at is None:
        refresh_session.revoked_at = now_utc
        refresh_session.last_used_at = now_utc
        await uow.refresh_tokens.save(refresh_session)
