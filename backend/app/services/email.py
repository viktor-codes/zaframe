"""
Отправка email через Resend.

Почему Resend:
- Простой API
- Бесплатный tier (100 писем/день)
- Надёжная доставка

Если RESEND_API_KEY не задан — логируем ссылку (для разработки).
"""

import structlog

from app.core.config import settings


async def send_magic_link_email(email: str, magic_link_url: str) -> bool:
    """
    Отправить Magic Link на email.

    Возвращает True при успехе, False при ошибке.
    Если RESEND_API_KEY не задан — логируем URL и возвращаем True (dev mode).
    """
    if not settings.RESEND_API_KEY:
        logger = structlog.get_logger(__name__)
        logger.info("magic_link_dev_mode_no_provider")
        return True

    logger = structlog.get_logger(__name__)
    try:
        import resend

        logger.debug(
            "resend_provider_enabled",
            resend_api_key_configured=True,
        )
        resend.api_key = settings.RESEND_API_KEY

        params: resend.Emails.SendParams = {
            "from": "ZaFrame <onboarding@resend.dev>",
            "to": [email],
            "subject": "Sign in to ZaFrame",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Sign in to ZaFrame</h2>
                <p>Click the link below to sign in to your account:</p>
                <p style="margin: 20px 0;">
                    <a href="{magic_link_url}" 
                       style="background-color: #45d1b8; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Sign in
                    </a>
                </p>
                <p style="color: #6b7280; font-size: 14px;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{magic_link_url}" style="color: #45d1b8; word-break: break-all;">
                        {magic_link_url}
                    </a>
                </p>
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                    This link expires in 15 minutes.<br>
                    If you didn't request this email, you can safely ignore it.
                </p>
            </div>
            """,
        }

        result = resend.Emails.send(params)
        logger.info(
            "magic_link_email_sent",
            resend_id=result.get("id", "unknown"),
        )
        return True
    except Exception as e:
        logger.error(
            "magic_link_email_send_failed",
            error_type=type(e).__name__,
        )
        if settings.DEBUG:
            # Safe for local dev: Resend returns API error text (domain, from, quota), not user PII.
            logger.warning(
                "magic_link_resend_error_detail",
                detail=str(e)[:800],
            )
        return False
