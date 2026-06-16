"""
Integration tests: concurrent occurrence locks do not deadlock.

CRIT-2 — course booking path and payment confirmation path share id-ASC lock order.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import DBAPIError
from tests.conftest import authenticate_via_otp

from app.core.database import async_session_maker
from app.core.uow import uow_scope
from app.modules.payment.service import confirm_order_after_payment

FROZEN_NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
CONCURRENT_ROUNDS = 8


async def _create_course_with_misordered_occurrences(
    client: AsyncClient,
) -> tuple[int, list[int]]:
    """
    Create occurrences where start_time order differs from id order.

    Later-created slot has earlier start_time → old start_time lock order
    would diverge from id-ASC order used by payment confirmation.
    """
    data = await authenticate_via_otp(client, email="crit2-deadlock@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Deadlock Test Studio",
            "description": "CRIT-2",
            "email": "deadlock-studio@example.com",
            "address": "Lock street 1",
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
            "name": "Deadlock Course",
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

    occurrence_ids: list[int] = []
    # Create later start first (higher id), then earlier start (lower id but later created)
    for days_ahead in (14, 7, 21):
        start = FROZEN_NOW + timedelta(days=days_ahead)
        end = start + timedelta(hours=1)
        r_occ = await client.post(
            "/api/v1/occurrences",
            json={
                "studio_id": studio_id,
                "service_id": service_id,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "title": "Session",
                "max_capacity": 10,
                "price_cents": 1500,
            },
            headers=headers,
        )
        assert r_occ.status_code == 201
        occurrence_ids.append(r_occ.json()["id"])

    return service_id, occurrence_ids


async def _create_pending_course_order(
    client: AsyncClient,
    *,
    service_id: int,
) -> int:
    with patch("app.services.service.utc_now", return_value=FROZEN_NOW):
        r = await client.post(
            "/api/v1/bookings",
            json={
                "service_id": service_id,
                "guest_name": "Pay Guest",
                "guest_email": "pay-guest@example.com",
                "guest_phone": "+100",
            },
        )
    assert r.status_code == 201, r.text
    return r.json()["order"]["id"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_course_and_payment_locks_do_not_deadlock(
    client: AsyncClient,
) -> None:
    service_id, occurrence_ids = await _create_course_with_misordered_occurrences(client)
    order_id = await _create_pending_course_order(client, service_id=service_id)

    start_barrier = asyncio.Barrier(2)
    errors: list[BaseException] = []

    async def lock_via_course_path() -> None:
        try:
            async with async_session_maker() as session:
                async with uow_scope(session=session, auto_commit=False) as uow:
                    await start_barrier.wait()
                    await uow.occurrences.list_active_future_by_service_for_update(
                        service_id,
                        now=FROZEN_NOW,
                    )
                    await asyncio.sleep(0.05)
                    await uow.commit()
        except BaseException as exc:
            errors.append(exc)

    async def lock_via_payment_path() -> None:
        try:
            async with async_session_maker() as session:
                async with uow_scope(session=session, auto_commit=False) as uow:
                    await start_barrier.wait()
                    for occurrence_id in sorted(occurrence_ids):
                        await uow.occurrences.get_by_id_for_update(occurrence_id)
                    await asyncio.sleep(0.05)
                    await uow.commit()
        except BaseException as exc:
            errors.append(exc)

    for _ in range(CONCURRENT_ROUNDS):
        start_barrier = asyncio.Barrier(2)
        errors.clear()
        await asyncio.gather(lock_via_course_path(), lock_via_payment_path())

        deadlock_errors = [
            exc
            for exc in errors
            if isinstance(exc, DBAPIError) and "deadlock" in str(exc.orig).lower()
        ]
        assert not deadlock_errors, f"Deadlock detected: {deadlock_errors}"
        assert not errors, f"Unexpected errors: {errors}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_confirm_order_and_course_booking_do_not_deadlock(
    client: AsyncClient,
) -> None:
    service_id, _ = await _create_course_with_misordered_occurrences(client)
    order_id = await _create_pending_course_order(client, service_id=service_id)

    start_barrier = asyncio.Barrier(2)
    errors: list[BaseException] = []

    async def confirm_payment() -> None:
        try:
            async with async_session_maker() as session:
                async with uow_scope(session=session, auto_commit=False) as uow:
                    await start_barrier.wait()
                    with patch("app.modules.payment.service.utc_now", return_value=FROZEN_NOW):
                        await confirm_order_after_payment(uow, order_id, payment_intent_id="pi_test")
                    await uow.commit()
        except BaseException as exc:
            errors.append(exc)

    async def book_another_course() -> None:
        try:
            async with async_session_maker() as session:
                async with uow_scope(session=session, auto_commit=False) as uow:
                    await start_barrier.wait()
                    await uow.occurrences.list_active_future_by_service_for_update(
                        service_id,
                        now=FROZEN_NOW,
                    )
                    await asyncio.sleep(0.05)
                    await uow.commit()
        except BaseException as exc:
            errors.append(exc)

    for _ in range(CONCURRENT_ROUNDS):
        start_barrier = asyncio.Barrier(2)
        errors.clear()
        await asyncio.gather(confirm_payment(), book_another_course())

        deadlock_errors = [
            exc
            for exc in errors
            if isinstance(exc, DBAPIError) and "deadlock" in str(exc.orig).lower()
        ]
        assert not deadlock_errors, f"Deadlock detected: {deadlock_errors}"
        assert not errors, f"Unexpected errors: {errors}"
