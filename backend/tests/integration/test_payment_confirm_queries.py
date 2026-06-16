"""
Integration tests: confirm_order_after_payment issues O(1) capacity count queries.

MID-3 — batch counts under occurrence lock instead of per-booking SQL.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from tests.conftest import authenticate_via_otp

from app.core.uow import create_uow, uow_scope
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence
from app.models.order import Order, OrderStatus
from app.modules.payment.service import (
    PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW,
    confirm_booking_after_payment,
    confirm_order_after_payment,
)

FROZEN_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
_SQL_LOGGER = "sqlalchemy.engine.Engine"


def _count_engine_sql_statements(caplog: pytest.LogCaptureFixture) -> int:
    """Count SQL statements logged by SQLAlchemy echo (exclude parameter-only lines)."""
    return sum(
        1
        for record in caplog.records
        if record.name == _SQL_LOGGER
        and record.levelno == logging.INFO
        and not record.getMessage().startswith("[")
    )


async def _count_confirm_order_queries(
    order_id: int,
    caplog: pytest.LogCaptureFixture,
) -> int:
    caplog.clear()
    async with uow_scope() as uow:
        await confirm_order_after_payment(uow, order_id, payment_intent_id="pi_query_test")
    return _count_engine_sql_statements(caplog)


async def _create_course_with_occurrence_count(
    client: AsyncClient,
    *,
    owner_email: str,
    occurrence_count: int,
) -> tuple[int, int]:
    """Return (service_id, order_id) for a pending course order."""
    data = await authenticate_via_otp(client, email=owner_email, name="Query Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Query Count Studio",
            "description": "MID-3",
            "email": "query-count@example.com",
            "address": "Query street 1",
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
            "name": f"Course {occurrence_count}",
            "type": "course",
            "duration_minutes": 60,
            "max_capacity": 10,
            "price_single_cents": 1500,
            "price_course_cents": 6000,
        },
        headers=headers,
    )
    assert r_service.status_code == 201
    service_id = r_service.json()["id"]

    for days_ahead in range(1, occurrence_count + 1):
        start = FROZEN_NOW + timedelta(days=days_ahead)
        end = start + timedelta(hours=1)
        r_occ = await client.post(
            "/api/v1/occurrences",
            json={
                "studio_id": studio_id,
                "service_id": service_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "title": f"Session {days_ahead}",
                "max_capacity": 10,
                "price_cents": 1500,
            },
            headers=headers,
        )
        assert r_occ.status_code == 201

    with patch("app.modules.catalog.service.service.utc_now", return_value=FROZEN_NOW):
        r_order = await client.post(
            "/api/v1/bookings",
            json={
                "service_id": service_id,
                "guest_name": "Query Guest",
                "guest_email": f"guest-{occurrence_count}@example.com",
                "guest_phone": "+100",
            },
        )
    assert r_order.status_code == 201, r_order.text
    return service_id, r_order.json()["order"]["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_order_issues_constant_number_of_queries(
    client: AsyncClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Extra pending bookings add lock queries only — not 2× capacity counts per booking.

    3 vs 9 occurrences: delta should stay small (≈ extra locks), not grow as 2× bookings.
    """
    caplog.set_level(logging.INFO, logger=_SQL_LOGGER)

    _, order_small = await _create_course_with_occurrence_count(
        client,
        owner_email="query-small@example.com",
        occurrence_count=3,
    )
    _, order_large = await _create_course_with_occurrence_count(
        client,
        owner_email="query-large@example.com",
        occurrence_count=9,
    )

    queries_small = await _count_confirm_order_queries(order_small, caplog)
    queries_large = await _count_confirm_order_queries(order_large, caplog)

    extra_occurrences = 6
    # Old path: ~3 SQL per extra booking (get_by_id + 2 counts) → delta ≥ 18.
    # New path: one batch counts + one lock per extra occurrence → delta ≈ 6.
    assert queries_large - queries_small <= extra_occurrences + 4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_confirm_order_overbooking_when_slot_full(
    client: AsyncClient,
    app_with_rollback_uow,
) -> None:
    """
    Order payment when occurrence is already full → manual review, no second CONFIRMED seat.
    """
    occurrence_id, _ = await _create_studio_and_single_occurrence(
        client,
        owner_email="order-overbook@example.com",
        max_capacity=1,
    )

    external_booking_id = await _create_guest_booking(
        client,
        occurrence_id,
        email="external@example.com",
    )

    session = app_with_rollback_uow.state._integration_session
    uow = create_uow(session)
    await confirm_booking_after_payment(
        uow,
        external_booking_id,
        payment_intent_id="pi_external",
    )
    await uow.bookings.flush()

    occurrence = await session.get(Occurrence, occurrence_id)
    assert occurrence is not None
    order = Order(
        studio_id=occurrence.studio_id,
        service_id=None,
        guest_email="course-guest@example.com",
        guest_name="Course Guest",
        total_amount_cents=2000,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    await session.flush()
    order_booking = Booking(
        occurrence_id=occurrence_id,
        order_id=order.id,
        guest_email="course-guest@example.com",
        guest_name="Course Guest",
        guest_phone="+102",
        status=BookingStatus.PENDING,
        reserved_until=FROZEN_NOW + timedelta(minutes=15),
    )
    session.add(order_booking)
    await session.flush()
    order_id = order.id

    uow = create_uow(session)
    with patch("app.modules.payment.service.utc_now", return_value=FROZEN_NOW):
        await confirm_order_after_payment(uow, order_id, payment_intent_id="pi_course_late")
    await uow.orders.flush()

    result = await session.execute(
        select(Booking).where(Booking.id == order_booking.id)
    )
    order_booking = result.scalar_one()
    assert order_booking.status == BookingStatus.CANCELLED
    assert order_booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW

    confirmed_count = await session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.occurrence_id == occurrence_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    assert confirmed_count == 1


async def _create_studio_and_single_occurrence(
    client: AsyncClient,
    *,
    owner_email: str,
    max_capacity: int,
) -> tuple[int, int]:
    data = await authenticate_via_otp(client, email=owner_email, name="Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Order Overbook Studio",
            "description": "MID-3 regression",
            "email": owner_email,
            "address": "Overbook 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    start = FROZEN_NOW + timedelta(days=3)
    end = start + timedelta(hours=1)
    r_occ = await client.post(
        "/api/v1/occurrences",
        json={
            "studio_id": studio_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Single seat",
            "max_capacity": max_capacity,
            "price_cents": 2000,
        },
        headers=headers,
    )
    assert r_occ.status_code == 201
    return r_occ.json()["id"], studio_id


async def _create_guest_booking(client: AsyncClient, occurrence_id: int, *, email: str) -> int:
    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Guest",
            "guest_email": email,
            "guest_phone": "+100",
        },
    )
    assert r_booking.status_code == 201
    return r_booking.json()["id"]
