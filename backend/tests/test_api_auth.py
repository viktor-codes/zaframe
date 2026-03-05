"""
Интеграционные тесты API аутентификации.

Требуют запущенную БД (DATABASE_URL) и SECRET_KEY в окружении.
"""
import re
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health():
    """Health endpoint без БД (без override)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        r = await ac.get("/api/v1/health")
    assert r.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_ready():
    """Readiness: проверка БД и опционально Stripe/Resend."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        r = await ac.get("/api/v1/health/ready")
    # При доступной БД — 200, иначе 503
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
    """POST /auth/magic-link/request возвращает 200 и не падает."""
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
    """GET /auth/magic-link/verify с неверным токеном — 400."""
    r = await client.get("/api/v1/auth/magic-link/verify", params={"token": "invalid-token"})
    assert r.status_code == 400
    assert "недействительна" in r.json().get("detail", "") or "истекла" in r.json().get("detail", "")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_auth_flow_refresh_logout_me(client):
    """
    Полный сценарий: запрос magic link -> верификация -> refresh -> /me -> logout -> старый refresh не работает.
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
    access = data2["access_token"]
    refresh = data2["refresh_token"]
    assert data2.get("token_type") == "bearer"
    assert "user" in data2
    assert data2["user"]["email"] == "flow@example.com"

    r3 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r3.status_code == 200
    assert r3.json()["email"] == "flow@example.com"

    r4 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r4.status_code == 200
    data4 = r4.json()
    new_access = data4["access_token"]
    new_refresh = data4["refresh_token"]
    # После ротации refresh обязательно новый; access может совпадать при выдаче в ту же секунду
    assert new_refresh != refresh

    r5 = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": new_refresh},
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert r5.status_code == 204

    r6 = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r6.status_code == 401

    r7 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r7.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_me_without_bearer_returns_401(client):
    """GET /auth/me без Authorization — 401."""
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(client):
    """POST /auth/refresh с невалидным refresh token — 401."""
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid-token"})
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_logout_without_auth_returns_401(client):
    """POST /auth/logout без Bearer — 401."""
    r = await client.post("/api/v1/auth/logout", json={"refresh_token": "any"})
    assert r.status_code == 401
