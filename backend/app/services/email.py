"""
Отправка email через Resend.

Если RESEND_API_KEY не задан — логируем код (dev mode).
"""

import structlog

from app.core.config import settings


async def send_otp_email(email: str, code: str) -> bool:
    """
    Send a numeric OTP to email.

    Returns True on success, False on provider error.
    Without RESEND_API_KEY logs the code for local development.
    """
    logger = structlog.get_logger(__name__)

    if not settings.RESEND_API_KEY:
        logger.info(
            "otp_dev_mode_no_provider",
            otp_code=code,
            otp_email=email,
        )
        return True

    try:
        import resend

        resend.api_key = settings.RESEND_API_KEY

        params: resend.Emails.SendParams = {
            "from": "ZaFrame <onboarding@resend.dev>",
            "to": [email],
            "subject": "Your ZaFrame sign-in code",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Sign in to ZaFrame</h2>
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
        logger.info("otp_email_sent", resend_id=result.get("id", "unknown"))
        return True
    except Exception as e:
        logger.error("otp_email_send_failed", error_type=type(e).__name__)
        if settings.DEBUG:
            logger.warning("otp_resend_error_detail", detail=str(e)[:800])
        return False
