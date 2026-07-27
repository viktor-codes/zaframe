"""
Integration tests: guest bookings attach to user after OTP verify.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp, create_test_service


@pytest.mark.integration
@pytest.mark.asyncio
async def test_otp_verify_attaches_guest_bookings_by_email(client: AsyncClient):
    """Guest booking gets user_id after OTP verify with matching email."""
    owner_email = "attach-owner@example.com"
    guest_email = "attach-guest@example.com"

    owner_data = await authenticate_via_otp(client, email=owner_email, name="Studio Owner")
    owner_headers = {"Authorization": f"Bearer {owner_data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Attach Studio",
            "description": "OTP attach test",
            "email": "studio@example.com",
            "address": "Attach street 1",
            "timezone": "Europe/Dublin",
        },
        headers=owner_headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]
    service_id = await create_test_service(
        client,
        headers=owner_headers,
        studio_id=studio_id,
        name="Attach Occurrence",
    )

    start = datetime.now(UTC) + timedelta(hours=3)
    end = start + timedelta(hours=1)
    r_occurrence = await client.post(
        "/api/v1/occurrences",
        json={
            "title": "Attach Occurrence",
            "description": "Test",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": service_id,
        },
        headers=owner_headers,
    )
    assert r_occurrence.status_code == 201
    occurrence_id = r_occurrence.json()["id"]

    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Guest User",
            "guest_email": guest_email,
            "guest_phone": "+111111111",
        },
    )
    assert r_booking.status_code == 201
    booking = r_booking.json()
    assert booking["user_id"] is None

    verify_data = await authenticate_via_otp(
        client,
        email=guest_email,
        name="Guest User",
    )
    guest_headers = {"Authorization": f"Bearer {verify_data['access_token']}"}

    r_booking_after = await client.get(
        f"/api/v1/bookings/{booking['id']}",
        headers=guest_headers,
    )
    assert r_booking_after.status_code == 200
    assert r_booking_after.json()["user_id"] == verify_data["user"]["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_otp_verify_attaches_only_specified_booking(client: AsyncClient):
    """booking_id on verify attaches one booking when email matches."""
    owner_email = "attach-specific-owner@example.com"
    guest_email = "attach-specific-guest@example.com"

    owner_data = await authenticate_via_otp(client, email=owner_email, name="Owner")
    owner_headers = {"Authorization": f"Bearer {owner_data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Specific Attach Studio",
            "timezone": "Europe/Dublin",
        },
        headers=owner_headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]
    service_id = await create_test_service(
        client,
        headers=owner_headers,
        studio_id=studio_id,
        name="Specific Attach Occurrence",
    )

    start = datetime.now(UTC) + timedelta(hours=4)
    end = start + timedelta(hours=1)

    async def create_occurrence(title: str) -> int:
        r_occurrence = await client.post(
            "/api/v1/occurrences",
            json={
                "title": title,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "max_capacity": 5,
                "price_cents": 500,
                "studio_id": studio_id,
                "service_id": service_id,
            },
            headers=owner_headers,
        )
        assert r_occurrence.status_code == 201
        return r_occurrence.json()["id"]

    slot_a = await create_occurrence("Occurrence A")
    slot_b = await create_occurrence("Occurrence B")

    async def create_guest_booking(occurrence_id: int) -> dict:
        r = await client.post(
            "/api/v1/bookings",
            json={
                "occurrence_id": occurrence_id,
                "guest_name": "Guest",
                "guest_email": guest_email,
            },
        )
        assert r.status_code == 201
        return r.json()

    booking_a = await create_guest_booking(slot_a)
    booking_b = await create_guest_booking(slot_b)

    captured_codes: list[str] = []

    async def capture_otp(_email: str, code: str) -> bool:
        captured_codes.append(code)
        return True

    with patch("app.modules.auth.otp.send_otp_email", side_effect=capture_otp):
        r_request = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": guest_email, "name": "Guest"},
        )
    assert r_request.status_code == 200

    r_verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={
            "email": guest_email,
            "code": captured_codes[0],
            "booking_id": booking_a["id"],
        },
    )
    assert r_verify.status_code == 200
    user_id = r_verify.json()["user"]["id"]
    guest_headers = {"Authorization": f"Bearer {r_verify.json()['access_token']}"}

    r_a = await client.get(f"/api/v1/bookings/{booking_a['id']}", headers=guest_headers)
    r_b = await client.get(f"/api/v1/bookings/{booking_b['id']}", headers=guest_headers)
    assert r_a.status_code == 200
    assert r_b.status_code == 200
    assert r_a.json()["user_id"] == user_id
    assert r_b.json()["user_id"] is None
