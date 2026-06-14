"""
Authentication business logic: email OTP and JWT sessions.
"""

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    generate_otp_code,
    get_otp_expires_at,
    get_user_id_from_access_token,
    hash_otp_code,
    parse_refresh_token,
)
from app.core.uow import UnitOfWork
from app.models.otp_code import OTPCode
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.booking import attach_guest_bookings
from app.services.email import send_otp_email
from app.services.user import get_or_create_user, get_user_by_id

_INVALID_OTP_MESSAGE = "Verification code is invalid or has expired"
_RATE_LIMIT_MESSAGE = "Too many verification codes requested. Try again later."


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
    since = now_utc - timedelta(hours=1)
    recent_count = await uow.otp_codes.count_recent_requests(email, since)
    if recent_count >= settings.OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR:
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
    await send_otp_email(email, code)


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
    code_hash = hash_otp_code(code)
    otp = await uow.otp_codes.get_active_by_email_and_hash(email, code_hash, now_utc)

    if otp is not None:
        if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            otp.used_at = now_utc
            await uow.otp_codes.save(otp)
            raise ValidationError(_INVALID_OTP_MESSAGE)
        return await _complete_otp_login(
            uow,
            otp,
            now_utc=now_utc,
            booking_id=booking_id,
        )

    latest = await uow.otp_codes.get_latest_active_for_email(email, now_utc)
    if latest is None:
        raise ValidationError(_INVALID_OTP_MESSAGE)

    latest.attempts += 1
    if latest.attempts >= settings.OTP_MAX_ATTEMPTS:
        latest.used_at = now_utc
    await uow.otp_codes.save(latest)
    raise ValidationError(_INVALID_OTP_MESSAGE)


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

    await attach_guest_bookings(uow, user, booking_id=booking_id)

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
    if refresh_session is None or not refresh_session.is_active(now_utc):
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
