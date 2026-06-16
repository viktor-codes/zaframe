"""
Rate limiting для чувствительных эндпоинтов (OTP, refresh и т.д.).

Используется SlowAPI; лимиты привязаны к IP (get_remote_address).
In-memory backend по умолчанию; при заданном REDIS_URL — shared storage для нескольких инстансов.
"""

from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _build_limiter() -> Limiter:
    kwargs: dict[str, Any] = {"key_func": get_remote_address}
    if settings.REDIS_URL:
        kwargs["storage_uri"] = settings.REDIS_URL
    return Limiter(**kwargs)


limiter = _build_limiter()
