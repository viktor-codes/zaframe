"""
Integration tests: course booking uses only active future occurrences.

CRIT-1 — booking set, pricing, and availability preview must match:
status=ACTIVE and start_time >= now.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.conftest import authenticate_via_otp

from app.services.service import (
    _calculate_course_order_total_cents,
    _distribute_course_unit_prices,
)
from app.models import Service, ServiceType

FROZEN_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)


@contextmanager
def frozen_utc_now():
    with patch("app.services.service.utc_now", return_value=FROZEN_NOW):
        yield FROZEN_NOW


async def _create_studio_and_course(
    client: AsyncClient,
    *,
    email: str,
    price_course_cents: int = 8000,
    price_single_cents: int = 1500,
) -> tuple[dict[str, str], int, int]:
    data = await authenticate_via_otp(client, email=email, name="Course Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Course Booking Studio",
            "description": "CRIT-1 tests",
            "email": "course-studio@example.com",
            "address": "Course street 1",
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
            "name": "Yoga Course",
            "type": "course",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": price_single_cents,
            "price_course_cents": price_course_cents,
        },
        headers=headers,
    )
    assert r_service.status_code == 201
    return headers, studio_id, r_service.json()["id"]


async def _create_occurrence(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    studio_id: int,
    service_id: int,
    start_time: datetime,
    status: str | None = None,
) -> int:
    end_time = start_time + timedelta(hours=1)
    r = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "service_id": service_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "title": "Course session",
            "max_capacity": 10,
            "price_cents": 1500,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    occurrence_id = r.json()["id"]

    if status is not None:
        r_patch = await client.patch(
            f"/api/v1/occurrences/{occurrence_id}",
            json={"status": status},
            headers=headers,
        )
        assert r_patch.status_code == 200, r_patch.text

    return occurrence_id


async def _book_course(
    client: AsyncClient,
    *,
    service_id: int,
    guest_email: str = "course-guest@example.com",
) -> dict:
    r = await client.post(
        "/api/v1/bookings",
        json={
            "service_id": service_id,
            "guest_name": "Course Guest",
            "guest_email": guest_email,
            "guest_phone": "+100",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_course_order_persists_guest_phone(client: AsyncClient):
    """Course order stores guest_phone for owner-facing order responses."""
    headers, _studio_id, service_id = await _create_studio_and_course(
        client,
        email="mid5-guest-phone@example.com",
    )

    future_id = await _create_occurrence(
        client,
        headers,
        studio_id=_studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=3),
    )
    assert future_id

    with frozen_utc_now():
        result = await _book_course(
            client,
            service_id=service_id,
            guest_email="course-phone@example.com",
        )

    assert result["order"]["guest_phone"] == "+100"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_course_booking_skips_past_occurrences(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="crit1-past@example.com",
    )

    past_id = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW - timedelta(days=7),
    )
    future_id_1 = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=3),
    )
    future_id_2 = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=10),
    )

    with frozen_utc_now():
        result = await _book_course(client, service_id=service_id)

    booked_occurrence_ids = {booking["occurrence_id"] for booking in result["bookings"]}
    assert booked_occurrence_ids == {future_id_1, future_id_2}
    assert past_id not in booked_occurrence_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_course_booking_skips_cancelled_occurrences(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="crit1-cancelled@example.com",
    )

    future_active_id = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=2),
    )
    future_cancelled_id = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=5),
        status="cancelled",
    )

    with frozen_utc_now():
        result = await _book_course(client, service_id=service_id)

    booked_occurrence_ids = {booking["occurrence_id"] for booking in result["bookings"]}
    assert booked_occurrence_ids == {future_active_id}
    assert future_cancelled_id not in booked_occurrence_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_course_booking_price_matches_future_sessions_count(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="crit1-price@example.com",
        price_course_cents=8000,
        price_single_cents=1500,
    )

    await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW - timedelta(days=14),
    )
    await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW - timedelta(days=7),
    )
    await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=3),
    )
    await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=10),
    )

    with frozen_utc_now():
        result = await _book_course(client, service_id=service_id)

    bookings = result["bookings"]
    order = result["order"]
    assert len(bookings) == 2

    # 2 future sessions out of 4 active → proportional course price: 8000 * 2/4 = 4000
    expected_total = 4000
    assert order["total_amount_cents"] == expected_total

    service_stub = Service(
        studio_id=studio_id,
        name="Yoga Course",
        type=ServiceType.COURSE,
        duration_minutes=60,
        max_capacity=10,
        price_single_cents=1500,
        price_course_cents=8000,
    )
    assert (
        _calculate_course_order_total_cents(
            service_stub,
            bookable_occurrence_count=len(bookings),
            total_active_occurrence_count=4,
        )
        == expected_total
    )
    assert sum(_distribute_course_unit_prices(expected_total, len(bookings))) == expected_total


@pytest.mark.integration
@pytest.mark.asyncio
async def test_course_availability_matches_booking_set(client: AsyncClient):
    headers, studio_id, service_id = await _create_studio_and_course(
        client,
        email="crit1-availability@example.com",
    )

    await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW - timedelta(days=5),
    )
    future_start_1 = FROZEN_NOW + timedelta(days=4)
    future_start_2 = FROZEN_NOW + timedelta(days=11)
    future_id_1 = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=future_start_1,
    )
    future_id_2 = await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=future_start_2,
    )
    await _create_occurrence(
        client,
        headers,
        studio_id=studio_id,
        service_id=service_id,
        start_time=FROZEN_NOW + timedelta(days=20),
        status="cancelled",
    )

    with frozen_utc_now():
        r_availability = await client.get(f"/api/v1/services/{service_id}/availability")
        assert r_availability.status_code == 200
        availability = r_availability.json()

        result = await _book_course(
            client,
            service_id=service_id,
            guest_email="availability-guest@example.com",
        )

    preview_dates = {item["date"] for item in availability["schedule_details"]}
    expected_dates = {
        future_start_1.date().isoformat(),
        future_start_2.date().isoformat(),
    }
    assert preview_dates == expected_dates
    assert len(availability["schedule_details"]) == len(result["bookings"])

    booked_ids = {booking["occurrence_id"] for booking in result["bookings"]}
    assert booked_ids == {future_id_1, future_id_2}
