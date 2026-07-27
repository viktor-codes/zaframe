"""
Rate limiting for sensitive endpoints such as OTP and refresh.

Uses SlowAPI; limits are keyed by client IP (see get_client_ip_for_rate_limit).
REDIS_URL enables shared storage across instances and is required in production
unless ALLOW_INMEMORY_RATE_LIMIT=true (see production_guards).
"""

from typing import Any

from slowapi import Limiter
from starlette.requests import Request

from app.core.client_ip import get_client_ip_for_rate_limit
from app.core.config import settings


def _rate_limit_key(request: Request) -> str:
    return get_client_ip_for_rate_limit(request)


def _build_limiter() -> Limiter:
    kwargs: dict[str, Any] = {"key_func": _rate_limit_key}
    if settings.REDIS_URL:
        kwargs["storage_uri"] = settings.REDIS_URL
    return Limiter(**kwargs)


limiter = _build_limiter()
