"""
Integration tests for authentication API.

Requires DATABASE_URL and SECRET_KEY in the environment.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from tests.conftest import authenticate_via_otp

from app.core.config import settings
from app.core.uow_factory import create_uow
from app.main import app
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence
from app.models.refresh_token import RefreshToken
from app.models.service import Service
from app.models.studio import Studio


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
    assert r.json()["version"] == settings.APP_VERSION


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
async def test_security_headers_hsts_only_in_production(monkeypatch):
    """HSTS is production-only so local HTTP clients keep working."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
        dev_response = await ac.get("/metrics")

        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        prod_response = await ac.get("/metrics")

    assert "strict-transport-security" not in dev_response.headers
    assert (
        prod_response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_docs_open_without_api_csp(monkeypatch):
    """Swagger UI keeps working because API CSP is skipped for docs paths."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text
    assert "content-security-policy" not in response.headers


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_returns_200():
    """Prometheus metrics endpoint is available without auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_otp_request_returns_200(client):
    """POST /auth/otp/request returns 200."""
    with patch("app.modules.auth.service.send_otp_email", new_callable=AsyncMock):
        r = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "test-auth@example.com", "name": "Test User"},
        )
    assert r.status_code == 200
    data = r.json()
    assert "message" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_otp_request_delivery_failure_returns_503(client):
    """POST /auth/otp/request fails honestly when email delivery is unavailable."""
    with patch("app.modules.auth.service.send_otp_email", AsyncMock(return_value=False)):
        response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "delivery-failed@example.com", "name": "Delivery Failed"},
        )

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == 503
    assert "could not be sent" in data["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_otp_verify_invalid_code_returns_400(client):
    """POST /auth/otp/verify with invalid code returns 400."""
    with patch("app.modules.auth.service.send_otp_email", new_callable=AsyncMock):
        await client.post(
            "/api/v1/auth/otp/request",
            json={"email": "invalid-otp@example.com", "name": "Test User"},
        )
    r = await client.post(
        "/api/v1/auth/otp/verify",
        json={"email": "invalid-otp@example.com", "code": "000000"},
    )
    assert r.status_code == 400
    detail = r.json().get("detail", "")
    assert "invalid" in detail.lower() or "expired" in detail.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_auth_flow_refresh_logout_me(client):
    """
    Full flow: OTP request -> verify (cookie) -> refresh -> /me -> logout
    -> old refresh no longer works.
    """
    data2 = await authenticate_via_otp(
        client,
        email="flow@example.com",
        name="Flow User",
    )
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
async def test_refresh_token_reuse_revokes_all_active_sessions(client, app_with_rollback_uow):
    """Reusing a rotated refresh token revokes the user's active refresh sessions."""
    suffix = uuid4().hex[:8]
    auth_data = await authenticate_via_otp(
        client,
        email=f"reuse-detected-{suffix}@example.com",
        name="Reuse Detected",
    )
    user_id = auth_data["user"]["id"]
    old_refresh_cookie = client.cookies.get("refresh_token")
    old_csrf_cookie = client.cookies.get("csrf_token")
    assert old_refresh_cookie is not None
    assert old_csrf_cookie is not None

    rotation_response = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": old_csrf_cookie},
    )
    assert rotation_response.status_code == 200
    new_refresh_cookie = client.cookies.get("refresh_token")
    new_csrf_cookie = client.cookies.get("csrf_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != old_refresh_cookie
    assert new_csrf_cookie is not None
    assert new_csrf_cookie != old_csrf_cookie

    reuse_response = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "X-CSRF-Token": old_csrf_cookie,
            "Cookie": f"refresh_token={old_refresh_cookie}; csrf_token={old_csrf_cookie}",
        },
    )
    assert reuse_response.status_code == 401

    current_session_response = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "X-CSRF-Token": new_csrf_cookie,
            "Cookie": f"refresh_token={new_refresh_cookie}; csrf_token={new_csrf_cookie}",
        },
    )
    assert current_session_response.status_code == 401

    session = app_with_rollback_uow.state._integration_session
    refresh_sessions = (
        (await session.execute(select(RefreshToken).where(RefreshToken.user_id == user_id)))
        .scalars()
        .all()
    )
    assert refresh_sessions
    assert all(refresh_session.revoked_at is not None for refresh_session in refresh_sessions)


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
    assert r.status_code in (401, 403)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refresh_missing_csrf_header_returns_403(client):
    """POST /auth/refresh without CSRF header returns 403 (double-submit)."""
    await authenticate_via_otp(client, email="csrf@example.com", name="CSRF User")
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patch_auth_me_updates_marketing_consent(client):
    """PATCH /auth/me updates privacy consent alongside editable profile fields."""
    suffix = uuid4().hex[:8]
    auth_data = await authenticate_via_otp(
        client,
        email=f"privacy-update-{suffix}@example.com",
        name="Privacy User",
    )
    headers = {"Authorization": f"Bearer {auth_data['access_token']}"}

    response = await client.patch(
        "/api/v1/auth/me",
        json={"marketing_consent": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["marketing_consent"] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_account_soft_deletes_user_and_revokes_sessions(client, app_with_rollback_uow):
    """
    Deleting an account hides the user from normal auth lookups and preserves history rows.
    """
    suffix = uuid4().hex[:8]
    email = f"delete-account-{suffix}@example.com"
    auth_data = await authenticate_via_otp(client, email=email, name="Deleted User")
    access_token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    refresh_cookie = client.cookies.get("refresh_token")
    csrf_cookie = client.cookies.get("csrf_token")
    assert refresh_cookie is not None
    assert csrf_cookie is not None

    session = app_with_rollback_uow.state._integration_session
    uow = create_uow(session)
    studio = await uow.studios.add(
        Studio(
            owner_id=user_id,
            name=f"Privacy Studio {suffix}",
            slug=f"privacy-studio-{suffix}",
            email=f"studio-{suffix}@example.com",
            timezone="Europe/Dublin",
        )
    )
    service = await uow.services.add(
        Service(
            studio_id=studio.id,
            name="Privacy Service",
            duration_minutes=60,
            max_capacity=10,
            price_single_cents=1500,
        )
    )
    occurrence = await uow.occurrences.add(
        Occurrence(
            studio_id=studio.id,
            service_id=service.id,
            start_time=datetime.now(UTC) + timedelta(days=1),
            end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
            title="Privacy Session",
            max_capacity=10,
            price_cents=1500,
        )
    )
    booking = await uow.bookings.add(
        Booking(
            occurrence_id=occurrence.id,
            user_id=user_id,
            guest_name="Deleted User",
            guest_email=email,
            status=BookingStatus.CONFIRMED,
        )
    )
    booking_id = booking.id

    pre_delete_codes: list[str] = []

    async def capture_pre_delete_otp(to: str, code: str) -> bool:
        pre_delete_codes.append(code)
        return True

    with patch("app.modules.auth.service.send_otp_email", side_effect=capture_pre_delete_otp):
        pre_delete_otp_response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": email, "name": "Deleted User"},
        )
    assert pre_delete_otp_response.status_code == 200
    assert len(pre_delete_codes) == 1

    delete_response = await client.post(
        "/api/v1/me/delete-account",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert delete_response.status_code == 204
    assert client.cookies.get("refresh_token") is None
    assert client.cookies.get("csrf_token") is None

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        headers={
            "X-CSRF-Token": csrf_cookie,
            "Cookie": f"refresh_token={refresh_cookie}; csrf_token={csrf_cookie}",
        },
    )
    assert refresh_response.status_code == 401

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 401

    lookup_uow = create_uow(session)
    assert await lookup_uow.users.get_by_id(user_id) is None
    deleted_user = await lookup_uow.users.get_by_id_including_deleted(user_id)
    assert deleted_user is not None
    assert deleted_user.deleted_at is not None
    assert deleted_user.email == f"deleted+{user_id}@deleted.local"
    assert deleted_user.name is None
    assert deleted_user.phone is None

    persisted_booking = (
        await session.execute(select(Booking).where(Booking.id == booking_id))
    ).scalar_one_or_none()
    assert persisted_booking is not None
    assert persisted_booking.user_id == user_id
    assert persisted_booking.guest_email == email

    login_response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"email": email, "code": pre_delete_codes[0]},
    )
    assert login_response.status_code == 400

    captured_codes: list[str] = []

    async def capture_otp(to: str, code: str) -> bool:
        captured_codes.append(code)
        return True

    with patch("app.modules.auth.service.send_otp_email", side_effect=capture_otp):
        otp_response = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": email, "name": "Deleted User"},
        )
    assert otp_response.status_code == 200
    assert len(captured_codes) == 1

    new_login_response = await client.post(
        "/api/v1/auth/otp/verify",
        json={"email": email, "code": captured_codes[0]},
    )
    assert new_login_response.status_code == 200
    new_user = new_login_response.json()["user"]
    assert new_user["id"] != user_id
    assert new_user["email"] == email
