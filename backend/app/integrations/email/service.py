"""
Email delivery via Resend.

Without RESEND_API_KEY: dev accepts the request without logging the OTP; production returns False.
"""

from __future__ import annotations

import asyncio

import structlog

from app.core.config import settings

_RESEND_TIMEOUT_SECONDS = 10.0


def _mask_email(email: str) -> str:
    """Mask email for logs, e.g. john@domain.com -> j***@d***.com."""
    local, sep, domain = email.partition("@")
    if not sep:
        return "***"

    masked_local = f"{local[0]}***" if local else "***"
    domain_name, dot, tld = domain.rpartition(".")
    if dot:
        masked_domain = f"{domain_name[0]}***.{tld}" if domain_name else f"***.{tld}"
    else:
        masked_domain = f"{domain[0]}***" if domain else "***"
    return f"{masked_local}@{masked_domain}"


def _send_otp_via_resend(email: str, code: str) -> str | None:
    """Blocking Resend send; intended to run via asyncio.to_thread."""
    import resend

    resend.api_key = settings.RESEND_API_KEY
    params: resend.Emails.SendParams = {
        "from": settings.EMAIL_FROM,
        "to": [email],
        "subject": "Your ZeeFrame sign-in code",
        "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Sign in to ZeeFrame</h2>
                <p>Enter this code to continue:</p>
                <p style="font-size: 32px; font-weight: bold; letter-spacing: 8px;
                          color: #2c3e50; margin: 24px 0;">
                    {code}
                </p>
                <p style="color: #6b7280; font-size: 14px;">
                    This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.<br>
                    If you didn't request this email, you can safely ignore it.
                </p>
            </div>
            """,
    }
    result = resend.Emails.send(params)
    return result.get("id")


async def send_otp_email(email: str, code: str) -> bool:
    """
    Send a numeric OTP to email.

    Returns True on success, False on provider error or missing provider in production.
    Without RESEND_API_KEY and DEBUG=True accepts the request without provider delivery.
    """
    logger = structlog.get_logger(__name__)

    if not settings.RESEND_API_KEY:
        if settings.DEBUG:
            logger.info(
                "otp_dev_mode_no_provider",
                otp_email_masked=_mask_email(email),
            )
            return True

        logger.error("otp_provider_not_configured")
        return False

    try:
        # WHY: Resend SDK is sync; never block the uvicorn event loop.
        resend_id = await asyncio.wait_for(
            asyncio.to_thread(_send_otp_via_resend, email, code),
            timeout=_RESEND_TIMEOUT_SECONDS,
        )
        logger.info("otp_email_sent", resend_id=resend_id or "unknown")
        return True
    except Exception as e:
        logger.error("otp_email_send_failed", error_type=type(e).__name__)
        if settings.DEBUG:
            logger.warning("otp_resend_error_detail", detail=str(e)[:800])
        return False
