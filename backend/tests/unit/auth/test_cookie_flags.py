"""Unit tests for auth cookie Secure / clear attributes."""

from __future__ import annotations

from starlette.responses import Response

from app.core.config import Settings
from app.modules.auth.router import (
    CSRF_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    _clear_refresh_cookie,
)


def test_cookie_secure_true_outside_dev() -> None:
    assert Settings(SECRET_KEY="x" * 32, ENVIRONMENT="dev").cookie_secure is False
    assert Settings(SECRET_KEY="x" * 32, ENVIRONMENT="staging").cookie_secure is True
    assert Settings(SECRET_KEY="x" * 32, ENVIRONMENT="production").cookie_secure is True


def test_clear_refresh_cookie_matches_set_cookie_flags(monkeypatch) -> None:
    from app.modules.auth import router as auth_router

    monkeypatch.setattr(auth_router.settings, "ENVIRONMENT", "staging")

    response = Response()
    _clear_refresh_cookie(response)

    # Starlette encodes delete as Set-Cookie with Max-Age=0 / expires.
    set_cookie_headers = response.headers.getlist("set-cookie")
    assert len(set_cookie_headers) == 2
    joined = "\n".join(set_cookie_headers)
    assert REFRESH_TOKEN_COOKIE_NAME in joined
    assert CSRF_COOKIE_NAME in joined
    assert "Secure" in joined
    assert "SameSite=lax" in joined or "SameSite=Lax" in joined
