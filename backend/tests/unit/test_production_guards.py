"""Unit tests for production startup guards."""

import pytest

from app.core.config import settings
from app.core.production_guards import (
    api_docs_route_kwargs,
    validate_production_rate_limit_config,
)


def test_api_docs_enabled_only_in_dev() -> None:
    assert api_docs_route_kwargs("dev") == {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }
    assert api_docs_route_kwargs("staging") == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }
    assert api_docs_route_kwargs("production") == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


def test_validate_rate_limit_allows_dev_without_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
    monkeypatch.setattr(settings, "REDIS_URL", None)
    monkeypatch.setattr(settings, "ALLOW_INMEMORY_RATE_LIMIT", False)
    validate_production_rate_limit_config()


def test_validate_rate_limit_requires_redis_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "REDIS_URL", None)
    monkeypatch.setattr(settings, "ALLOW_INMEMORY_RATE_LIMIT", False)
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        validate_production_rate_limit_config()


def test_validate_rate_limit_allows_explicit_inmemory_escape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "REDIS_URL", None)
    monkeypatch.setattr(settings, "ALLOW_INMEMORY_RATE_LIMIT", True)
    validate_production_rate_limit_config()


def test_validate_rate_limit_ok_with_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOW_INMEMORY_RATE_LIMIT", False)
    validate_production_rate_limit_config()


def test_cookie_samesite_is_lax_for_same_origin_proxy() -> None:
    """Auth cookies land on the Next origin via /api rewrite — Lax, not None."""
    assert settings.cookie_samesite == "lax"
