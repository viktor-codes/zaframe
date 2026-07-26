"""Smoke tests for SlowAPI Redis storage wiring."""

from slowapi import Limiter
from slowapi.util import get_remote_address


def test_limiter_accepts_redis_storage_uri_without_missing_dep() -> None:
    """
    REDIS_URL requires the redis package at Limiter construction time.

    This catches the production footgun where storage_uri is set but redis
    is not installed (ConfigurationError from limits).
    """
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379/0",
    )
    assert limiter is not None
