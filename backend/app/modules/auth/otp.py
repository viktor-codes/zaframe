"""Email OTP request and verification."""

from datetime import datetime, timedelta

import structlog

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.core.observability import log_domain_event
from app.core.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    generate_otp_code,
    get_otp_expires_at,
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
from app.modules.identity import get_or_create_user

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

    WHY: commit the OTP row before calling Resend so (1) a delivery failure cannot
    roll back a code the provider already accepted, and (2) the DB lock/connection
    is not held for the duration of the sync email SDK call.
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
    await uow.commit()

    email_sent = await send_otp_email(email, code)
    if not email_sent:
        log_domain_event(
            logger,
            "otp_delivery_unavailable",
            level="error",
            user_id=existing_user.id if existing_user is not None else None,
        )
        # WHY: never leave a usable OTP when the user never received the email.
        await uow.otp_codes.invalidate_active_for_email(email, utc_now())
        await uow.commit()
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
