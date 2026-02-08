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

        resend.api_key = settings.RESEND_API_KEY
        params = resend.Emails.send({
            "from": "ZaFrame <onboarding@resend.dev>",
            "to": [email],
            "subject": "Вход в ZaFrame — ссылка для входа",
            "html": f"""
            <p>Здравствуйте!</p>
            <p>Нажмите на ссылку ниже, чтобы войти в ZaFrame:</p>
            <p><a href="{magic_link_url}">{magic_link_url}</a></p>
            <p>Ссылка действительна 15 минут.</p>
            <p>Если вы не запрашивали вход, проигнорируйте это письмо.</p>
            """,
        })
        return True
    except Exception as e:
        logger.exception("Failed to send magic link email: %s", e)
        return False
