"""
JWT и Magic Link: создание и проверка токенов.

Почему python-jose:
- Стандартная библиотека для JWT в Python
- Поддержка HS256, RS256
- Простой API: encode/decode
"""
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    user_id: int,
    email: str,
) -> str:
    """Создать access token (короткоживущий)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    """Создать refresh token (долгоживущий)."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict | None:
    """
    Декодировать и проверить JWT.
    Возвращает payload или None при ошибке.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def get_user_id_from_access_token(token: str) -> int | None:
    """Извлечь user_id из access token."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None
    try:
        return int(payload["sub"])
    except (ValueError, KeyError):
        return None


def get_user_id_from_refresh_token(token: str) -> int | None:
    """Извлечь user_id из refresh token."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None
    try:
        return int(payload["sub"])
    except (ValueError, KeyError):
        return None


def generate_magic_link_token() -> str:
    """Сгенерировать криптографически стойкий токен для Magic Link."""
    return token_urlsafe(32)


def get_magic_link_expires_at() -> datetime:
    """
    Время истечения Magic Link токена.
    
    Возвращает naive datetime (без timezone) для совместимости с TIMESTAMP WITHOUT TIME ZONE.
    """
    utc_now = datetime.now(timezone.utc)
    expires_at = utc_now + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES)
    # Преобразуем в naive datetime (убираем timezone) для БД
    return expires_at.replace(tzinfo=None)
