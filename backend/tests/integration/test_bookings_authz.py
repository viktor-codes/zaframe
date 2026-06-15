"""
Authorization tests for booking endpoints.

Covers anonymous 401, foreign-user 404 on single booking, studio-owner views,
and guest booking visibility after OTP login.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp


async def _authenticate_user(
    client: AsyncClient,
    email: str,
    name: str = "Test User",
) -> tuple[str, dict]:
    data = await authenticate_via_otp(client, email=email, name=name)
    return data["access_token"], data["user"]


async def _create_studio_slot_and_booking(
    client: AsyncClient,
    owner_headers: dict[str, str],
    *,
    guest_email: str = "guest@example.com",
) -> tuple[int, int, int]:
    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Authz Studio",
            "description": "For authz tests",
            "email": "authz-studio@example.com",
            "address": "Authz street 1",
            "timezone": "Europe/Dublin",
        },
        headers=owner_headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    start = datetime.now(UTC) + timedelta(hours=3)
    end = start + timedelta(hours=1)
    r_slot = await client.post(
        "/api/v1/slots",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Authz Class",
            "description": "Test slot",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": None,
        },
        headers=owner_headers,
    )
    assert r_slot.status_code == 201
    slot_id = r_slot.json()["id"]

    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "slot_id": slot_id,
            "guest_name": "Guest User",
            "guest_email": guest_email,
            "guest_phone": "+111111111",
        },
    )
    assert r_booking.status_code == 201
    booking_id = r_booking.json()["id"]
    return studio_id, slot_id, booking_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_anonymous_booking_endpoints_return_401(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-anon@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    _, slot_id, booking_id = await _create_studio_slot_and_booking(client, owner_headers)

    assert (await client.get("/api/v1/bookings")).status_code == 401
    assert (await client.get(f"/api/v1/bookings/{booking_id}")).status_code == 401
    assert (await client.get("/api/v1/bookings/count")).status_code == 401
    assert (await client.patch(f"/api/v1/bookings/{booking_id}/cancel")).status_code == 401
    assert (await client.get(f"/api/v1/slots/{slot_id}/bookings")).status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_foreign_user_gets_404_on_foreign_booking(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-404@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    _, _, booking_id = await _create_studio_slot_and_booking(
        client, owner_headers, guest_email="real-guest-authz@example.com"
    )

    stranger_access, _ = await _authenticate_user(client, "stranger-authz-404@example.com")
    stranger_headers = {"Authorization": f"Bearer {stranger_access}"}

    assert (
        await client.get(f"/api/v1/bookings/{booking_id}", headers=stranger_headers)
    ).status_code == 404
    assert (
        await client.patch(f"/api/v1/bookings/{booking_id}/cancel", headers=stranger_headers)
    ).status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_foreign_user_gets_403_on_foreign_slot_bookings(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-slot-403@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    _, slot_id, _ = await _create_studio_slot_and_booking(client, owner_headers)

    stranger_access, _ = await _authenticate_user(client, "stranger-authz-slot-403@example.com")
    stranger_headers = {"Authorization": f"Bearer {stranger_access}"}

    assert (
        await client.get(f"/api/v1/slots/{slot_id}/bookings", headers=stranger_headers)
    ).status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_can_view_and_cancel_own_booking(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-guest@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    guest_email = "guest-authz-own@example.com"
    _, _, booking_id = await _create_studio_slot_and_booking(
        client, owner_headers, guest_email=guest_email
    )

    guest_access, _ = await _authenticate_user(client, guest_email)
    guest_headers = {"Authorization": f"Bearer {guest_access}"}

    r_get = await client.get(f"/api/v1/bookings/{booking_id}", headers=guest_headers)
    assert r_get.status_code == 200
    assert r_get.json()["guest_email"] == guest_email

    r_cancel = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=guest_headers,
    )
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "cancelled"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_studio_owner_sees_slot_bookings_and_single_booking(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-view@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    _, slot_id, booking_id = await _create_studio_slot_and_booking(
        client, owner_headers, guest_email="participant-authz@example.com"
    )

    r_list = await client.get(f"/api/v1/slots/{slot_id}/bookings", headers=owner_headers)
    assert r_list.status_code == 200
    bookings = r_list.json()
    assert len(bookings) == 1
    assert bookings[0]["id"] == booking_id
    assert bookings[0]["guest_email"] == "participant-authz@example.com"

    r_owner_list = await client.get("/api/v1/bookings", headers=owner_headers)
    assert r_owner_list.status_code == 200
    assert any(b["id"] == booking_id for b in r_owner_list.json())

    r_get = await client.get(f"/api/v1/bookings/{booking_id}", headers=owner_headers)
    assert r_get.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_owner_list_excludes_foreign_studio_bookings(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-list@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    _, _, booking_id = await _create_studio_slot_and_booking(client, owner_headers)

    stranger_access, _ = await _authenticate_user(client, "stranger-authz-list@example.com")
    stranger_headers = {"Authorization": f"Bearer {stranger_access}"}

    r_list = await client.get("/api/v1/bookings", headers=stranger_headers)
    assert r_list.status_code == 200
    assert all(b["id"] != booking_id for b in r_list.json())


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_booking_visible_in_my_after_otp_login(client: AsyncClient):
    owner_access, _ = await _authenticate_user(client, "owner-authz-my@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_access}"}
    guest_email = "guest-authz-my@example.com"
    _, _, booking_id = await _create_studio_slot_and_booking(
        client, owner_headers, guest_email=guest_email
    )

    guest_access, _ = await _authenticate_user(client, guest_email, name="Guest User")
    guest_headers = {"Authorization": f"Bearer {guest_access}"}

    r_my = await client.get("/api/v1/bookings/my", headers=guest_headers)
    assert r_my.status_code == 200
    my_ids = [item["id"] for item in r_my.json()]
    assert booking_id in my_ids
