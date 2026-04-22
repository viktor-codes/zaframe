"""
Integration tests for authentication API.

Requires DATABASE_URL and SECRET_KEY in the environment.
"""

import re
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health():
    """Health endpoint without DB override."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        r = await ac.get("/api/v1/health")
    assert r.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_ready():
    """Readiness: DB check and optional Stripe/Resend."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        r = await ac.get("/api/v1/health/ready")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    if r.status_code == 200:
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "ok"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_magic_link_request_returns_200(client):
    """POST /auth/magic-link/request returns 200."""
    with patch("app.services.auth.send_magic_link_email", new_callable=AsyncMock):
        r = await client.post(
            "/api/v1/auth/magic-link/request",
            json={"email": "test-auth@example.com", "name": "Test User"},
        )
    assert r.status_code == 200
    data = r.json()
    assert "message" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_magic_link_verify_invalid_token_returns_400(client):
    """GET /auth/magic-link/verify with invalid token returns 400."""
    r = await client.get("/api/v1/auth/magic-link/verify", params={"token": "invalid-token"})
    assert r.status_code == 400
    detail = r.json().get("detail", "")
    assert "invalid" in detail.lower() or "expired" in detail.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_auth_flow_refresh_logout_me(client):
    """
    Full flow: magic link request -> verify (cookie) -> refresh -> /me -> logout
    -> old refresh no longer works.
    """
    captured_url = []

    async def capture_email(to: str, url: str) -> None:
        captured_url.append(url)

    with patch("app.services.auth.send_magic_link_email", side_effect=capture_email):
        r1 = await client.post(
            "/api/v1/auth/magic-link/request",
            json={"email": "flow@example.com", "name": "Flow User"},
        )
    assert r1.status_code == 200
    assert len(captured_url) == 1
    match = re.search(r"token=([^&]+)", captured_url[0])
    assert match
    token = match.group(1)

    r2 = await client.get("/api/v1/auth/magic-link/verify", params={"token": token})
    assert r2.status_code == 200
    data2 = r2.json()
    assert "refresh_token" not in data2
    access = data2["access_token"]
    assert data2.get("token_type") == "bearer"
    assert "user" in data2
    assert data2["user"]["email"] == "flow@example.com"
    refresh_cookie_after_verify = client.cookies.get("refresh_token")
    assert refresh_cookie_after_verify is not None
    csrf_cookie_after_verify = client.cookies.get("csrf_token")
    assert csrf_cookie_after_verify is not None

    r3 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r3.status_code == 200
    assert r3.json()["email"] == "flow@example.com"

    r4 = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": csrf_cookie_after_verify},
    )
    assert r4.status_code == 200
    data4 = r4.json()
    assert "refresh_token" not in data4
    new_access = data4["access_token"]
    refresh_cookie_after_refresh = client.cookies.get("refresh_token")
    assert refresh_cookie_after_refresh is not None
    assert refresh_cookie_after_refresh != refresh_cookie_after_verify
    csrf_cookie_after_refresh = client.cookies.get("csrf_token")
    assert csrf_cookie_after_refresh is not None
    assert csrf_cookie_after_refresh != csrf_cookie_after_verify

    r5 = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert r5.status_code == 204

    r6 = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": csrf_cookie_after_refresh},
    )
    assert r6.status_code in (401, 403)

    r7 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r7.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_without_bearer_returns_401(client):
    """GET /auth/me without Authorization returns 401."""
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401():
    """POST /auth/refresh without valid refresh cookie returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as fresh_client:
        r = await fresh_client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_missing_csrf_header_returns_403(client):
    """POST /auth/refresh without CSRF header returns 403 (double-submit)."""
    # Bootstrap cookies via verify
    captured_url = []

    async def capture_email(to: str, url: str) -> None:
        captured_url.append(url)

    with patch("app.services.auth.send_magic_link_email", side_effect=capture_email):
        r1 = await client.post(
            "/api/v1/auth/magic-link/request",
            json={"email": "csrf@example.com", "name": "CSRF User"},
        )
    assert r1.status_code == 200
    token = re.search(r"token=([^&]+)", captured_url[0]).group(1)
    r2 = await client.get("/api/v1/auth/magic-link/verify", params={"token": token})
    assert r2.status_code == 200
    assert client.cookies.get("refresh_token") is not None
    assert client.cookies.get("csrf_token") is not None

    r3 = await client.post("/api/v1/auth/refresh")
    assert r3.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_without_auth_returns_401(client):
    """POST /auth/logout without Bearer returns 401."""
    r = await client.post("/api/v1/auth/logout")
    assert r.status_code == 401
