"""
Integration tests: GET /api/v1/orders/{order_id} for success-page poll.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp

from app.core.uow_factory import create_uow
from app.main import app
from app.modules.payment.service import confirm_order_after_payment

FROZEN_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
_SECRET_FIELDS = frozenset(
    {"access_token", "payment_intent_id", "checkout_session_id"},
)


async def _create_studio_and_course(
    client: AsyncClient,
    *,
    email: str,
) -> tuple[dict[str, str], int, int]:
    data = await authenticate_via_otp(client, email=email, name="Order Get Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Order Get Studio",
            "description": "GET order by id",
            "email": "order-get@example.com",
            "address": "Order street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    r_service = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": "Order Get Course",
            "type": "course",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": 1500,
            "price_course_cents": 8000,
        },
        headers=headers,
    )
    assert r_service.status_code == 201
    return headers, studio_id, r_service.json()["id"]


async def _create_future_occurrence(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    studio_id: int,
    service_id: int,
) -> int:
    start = datetime.now(UTC) + timedelta(days=3)
    end = start + timedelta(hours=1)
    r = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "service_id": service_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Order get session",
            "max_capacity": 10,
            "price_cents": 1500,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _book_course_guest(
    client: AsyncClient,
    *,
    service_id: int,
    guest_email: str,
) -> dict:
    r = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": service_id,
            "guest_name": "Order Guest",
            "guest_email": guest_email,
            "guest_phone": "+100",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_get_order_with_access_token_returns_pending(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="order-get-guest@example.com",
    )
    await _create_future_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    created = await _book_course_guest(
        client,
        service_id=service_id,
        guest_email="poll-guest@example.com",
    )
    order_id = created["order"]["id"]
    access_token = created["access_token"]

    r = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == order_id
    assert body["status"] == "pending"
    assert body["service_id"] == service_id
    assert body["total_amount_cents"] > 0
    assert body["currency"]
    assert len(body["bookings"]) >= 1
    booking = body["bookings"][0]
    assert booking["status"] == "pending"
    assert "payment_status" in booking
    assert booking["reserved_until"] is not None
    assert _SECRET_FIELDS.isdisjoint(body.keys())
    assert "access_token" not in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_get_order_after_confirm_cleared_token_returns_404(
    client: AsyncClient,
):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="order-get-cleared@example.com",
    )
    await _create_future_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    created = await _book_course_guest(
        client,
        service_id=service_id,
        guest_email="cleared-guest@example.com",
    )
    order_id = created["order"]["id"]
    access_token = created["access_token"]

    session = app.state._integration_session
    uow = create_uow(session)
    ok = await confirm_order_after_payment(uow, order_id, payment_intent_id="pi_order_get")
    assert ok is True
    await session.commit()

    r = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_owner_get_order_by_user_id(client: AsyncClient):
    owner = await authenticate_via_otp(
        client,
        email="order-session-owner@example.com",
        name="Session Owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner['access_token']}"}

    # Separate studio owner creates the course catalog.
    studio_headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="order-get-catalog@example.com",
    )
    await _create_future_occurrence(
        client,
        studio_headers,
        studio_id=studio_id,
        service_id=service_id,
    )

    r_book = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": service_id,
            "guest_name": "Session Owner",
            "guest_email": "order-session-owner@example.com",
            "guest_phone": "+200",
        },
        headers=owner_headers,
    )
    assert r_book.status_code == 201, r_book.text
    order_id = r_book.json()["order"]["id"]

    r = await client.get(f"/api/v1/orders/{order_id}", headers=owner_headers)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == order_id
    assert r.json()["user_id"] == owner["user"]["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_email_merge_owner_get_order_without_user_id(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="order-get-merge-studio@example.com",
    )
    await _create_future_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    guest_email = "merge-owner@example.com"
    created = await _book_course_guest(
        client,
        service_id=service_id,
        guest_email=guest_email,
    )
    order_id = created["order"]["id"]
    assert created["order"]["user_id"] is None

    merged = await authenticate_via_otp(
        client,
        email=guest_email,
        name="Merge Owner",
    )
    r = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {merged['access_token']}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["guest_email"] == guest_email


@pytest.mark.integration
@pytest.mark.asyncio
async def test_stranger_jwt_get_order_returns_404(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="order-get-stranger-studio@example.com",
    )
    await _create_future_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    created = await _book_course_guest(
        client,
        service_id=service_id,
        guest_email="owned-by-guest@example.com",
    )
    order_id = created["order"]["id"]

    stranger = await authenticate_via_otp(
        client,
        email="stranger-order@example.com",
        name="Stranger",
    )
    r = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {stranger['access_token']}"},
    )
    assert r.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_order_without_auth_returns_401(client: AsyncClient):
    r = await client.get("/api/v1/orders/1")
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_order_idor_guessed_id_wrong_token_returns_404(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="order-get-idor@example.com",
    )
    await _create_future_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
    )
    created = await _book_course_guest(
        client,
        service_id=service_id,
        guest_email="idor-guest@example.com",
    )
    order_id = created["order"]["id"]

    r = await client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert r.status_code == 404
