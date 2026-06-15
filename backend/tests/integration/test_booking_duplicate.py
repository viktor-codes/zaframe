"""
Integration tests: duplicate booking protection per (slot, guest).

- Pre-check returns 400 before insert
- IntegrityError under concurrency returns 409
- Cancelled booking frees the slot for re-booking
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp

from app.core.database import async_session_maker
from app.core.exceptions import AppError, ConflictError, ValidationError
from app.core.uow import uow_scope
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.services.booking import (
    DUPLICATE_BOOKING_MESSAGE,
    create_booking,
)


async def _create_bookable_slot(
    client: AsyncClient,
    *,
    owner_email: str = "dup-owner@example.com",
    max_capacity: int = 5,
) -> int:
    """Create studio + future slot; return slot_id."""
    verify_data = await authenticate_via_otp(client, email=owner_email, name="Dup Owner")
    headers = {"Authorization": f"Bearer {verify_data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Dup Studio",
            "description": "Duplicate booking tests",
            "email": "dup-studio@example.com",
            "address": "Dup street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    start = datetime.now(UTC) + timedelta(hours=4)
    end = start + timedelta(hours=1)
    r_slot = await client.post(
        "/api/v1/slots",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Dup Class",
            "description": "Slot for duplicate tests",
            "max_capacity": max_capacity,
            "price_cents": 1500,
            "studio_id": studio_id,
            "service_id": None,
        },
        headers=headers,
    )
    assert r_slot.status_code == 201
    return r_slot.json()["id"]


def _booking_payload(slot_id: int, *, guest_email: str = "dup-guest@example.com") -> dict:
    return {
        "slot_id": slot_id,
        "guest_name": "Dup Guest",
        "guest_email": guest_email,
        "guest_phone": "+1234567890",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duplicate_booking_same_slot_returns_400(client: AsyncClient) -> None:
    """Second booking for the same slot and email is rejected before insert."""
    slot_id = await _create_bookable_slot(client)
    payload = _booking_payload(slot_id)

    r_first = await client.post("/api/v1/bookings", json=payload)
    assert r_first.status_code == 201

    r_second = await client.post("/api/v1/bookings", json=payload)
    assert r_second.status_code == 400
    assert r_second.json()["detail"] == DUPLICATE_BOOKING_MESSAGE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rebook_after_cancel_succeeds(client: AsyncClient) -> None:
    """Cancelled booking no longer blocks a new reservation on the same slot."""
    slot_id = await _create_bookable_slot(client, owner_email="rebook-owner@example.com")
    guest_email = "rebook-guest@example.com"
    payload = _booking_payload(slot_id, guest_email=guest_email)

    r_first = await client.post("/api/v1/bookings", json=payload)
    assert r_first.status_code == 201
    booking_id = r_first.json()["id"]

    guest_verify = await authenticate_via_otp(client, email=guest_email, name="Rebook Guest")
    guest_headers = {"Authorization": f"Bearer {guest_verify['access_token']}"}
    r_cancel = await client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=guest_headers,
    )
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "cancelled"

    r_second = await client.post("/api/v1/bookings", json=payload)
    assert r_second.status_code == 201
    assert r_second.json()["id"] != booking_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_booking_race_one_success_one_conflict(client: AsyncClient) -> None:
    """
    Parallel inserts: DB unique index rejects the loser with 409 Conflict.

    Pre-check is bypassed so both coroutines reach INSERT (TOCTOU race).
    """
    slot_id = await _create_bookable_slot(client, owner_email="race-owner@example.com")
    schema = BookingCreate(
        slot_id=slot_id,
        guest_name="Race Guest",
        guest_email="race-guest@example.com",
        guest_phone="+1999888777",
    )

    async def attempt() -> Booking | AppError:
        try:
            async with async_session_maker() as session:
                async with uow_scope(session=session) as uow:
                    return await create_booking(uow, schema)
        except (ConflictError, ValidationError) as exc:
            return exc

    with patch(
        "app.services.booking._ensure_no_active_booking_for_guest",
        new_callable=AsyncMock,
    ):
        results = await asyncio.gather(attempt(), attempt())

    successes = [r for r in results if isinstance(r, Booking)]
    conflicts = [r for r in results if isinstance(r, ConflictError)]
    assert len(successes) == 1
    assert len(conflicts) == 1
    assert conflicts[0].status_code == 409
    assert conflicts[0].detail == DUPLICATE_BOOKING_MESSAGE
