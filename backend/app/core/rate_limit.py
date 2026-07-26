"""
Rate limiting for sensitive endpoints such as OTP and refresh.

Uses SlowAPI; limits are bound to IP via get_remote_address.
REDIS_URL enables shared storage across instances and is required in production
unless ALLOW_INMEMORY_RATE_LIMIT=true (see production_guards).
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
