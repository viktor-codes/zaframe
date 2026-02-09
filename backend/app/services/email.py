"""
Отправка email через Resend.

Почему Resend:
- Простой API
- Бесплатный tier (100 писем/день)
- Надёжная доставка

Если RESEND_API_KEY не задан — логируем ссылку (для разработки).
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_magic_link_email(email: str, magic_link_url: str) -> bool:
    """
    Отправить Magic Link на email.

    Возвращает True при успехе, False при ошибке.
    Если RESEND_API_KEY не задан — логируем URL и возвращаем True (dev mode).
    """
    if not settings.RESEND_API_KEY:
        logger.info(
            "Magic Link (dev mode, no RESEND_API_KEY): %s",
            magic_link_url,
        )
        return True

    try:
        import resend

        logger.debug("Using Resend API key: %s...", settings.RESEND_API_KEY[:10])
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
            "Magic Link email sent successfully to %s. Resend ID: %s",
            email,
            result.get("id", "unknown"),
        )
        return True
    except Exception as e:
        logger.error(
            "Failed to send magic link email to %s: %s. Error type: %s",
            email,
            str(e),
            type(e).__name__,
        )
        logger.exception("Full traceback:")
        return False
