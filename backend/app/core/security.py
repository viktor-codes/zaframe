"""
JWT и Magic Link: создание и проверка токенов.

Почему python-jose:
- Стандартная библиотека для JWT в Python
- Поддержка HS256, RS256
- Простой API: encode/decode
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from jose import JWTError, jwt

from app.core.config import settings


def _utcnow() -> datetime:
    """Возвращает текущий момент времени в UTC (aware datetime)."""
    return datetime.now(UTC)


def create_access_token(
    user_id: int,
    email: str,
) -> str:
    """Создать access token (короткоживущий)."""
    now = _utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    """
    Создать refresh token (долгоживущий).

    Добавляем jti (unique JWT ID) для возможности последующей ротации
    и точечного отзыва конкретных refresh-токенов.
    """
    now = _utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = token_urlsafe(16)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "exp": expire,
        "iat": now,
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


@dataclass
class RefreshTokenData:
    """Структурированное содержимое refresh-токена после валидации."""

    user_id: int
    jti: str
    expires_at: datetime


def parse_refresh_token(token: str) -> RefreshTokenData | None:
    """
    Распарсить и провалидировать refresh-token.

    Возвращает RefreshTokenData или None, если токен недействителен.
    """
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None

    try:
        user_id = int(payload["sub"])
        jti = str(payload["jti"])
        exp_raw = payload["exp"]
        exp_ts = float(exp_raw)
        expires_at = datetime.fromtimestamp(exp_ts, tz=UTC)
    except (KeyError, TypeError, ValueError):
        return None

    return RefreshTokenData(user_id=user_id, jti=jti, expires_at=expires_at)


def generate_magic_link_token() -> str:
    """Сгенерировать криптографически стойкий токен для Magic Link."""
    return token_urlsafe(32)


def create_csrf_token() -> str:
    """
    Create a CSRF token for double-submit cookie pattern.

    Random, unguessable token stored in a non-httpOnly cookie and echoed by the client
    in X-CSRF-Token header for sensitive cookie-auth endpoints.
    """
    return token_urlsafe(32)


def hash_magic_link_token(token: str) -> str:
    """
    Получить безопасный хэш токена Magic Link для хранения в БД.

    Используем HMAC-SHA256 с SECRET_KEY как ключом, чтобы даже при компрометации
    дампа БД нельзя было восстановить исходный токен.
    """
    key = settings.SECRET_KEY.encode("utf-8")
    msg = token.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def get_magic_link_expires_at() -> datetime:
    """
    Время истечения Magic Link токена (aware datetime в UTC).
    """
    utc_now = _utcnow()
    return utc_now + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES)
