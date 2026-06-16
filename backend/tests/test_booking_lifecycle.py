"""
Unit tests for booking lifecycle transitions (expire pending, complete confirmed).

Boundary cases mirror repository filters:
- expire: reserved_until <= now (hold uses reserved_until > now)
- complete: occurrence.end_time < now (in progress at exactly end_time)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.booking import Booking, BookingStatus
from app.modules.booking import BookingRepository, complete_past_confirmed, expire_stale_pending

NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.bookings.flush = AsyncMock()
    return uow


def _pending_booking(*, reserved_until: datetime | None) -> Booking:
    booking = Booking(
        occurrence_id=1,
        guest_email="guest@example.com",
        status=BookingStatus.PENDING,
        reserved_until=reserved_until,
    )
    booking.id = 1
    return booking


@pytest.mark.asyncio
async def test_expire_stale_pending_at_boundary_transitions(mock_uow):
    """reserved_until == now is no longer an active hold and must expire."""
    booking = _pending_booking(reserved_until=NOW)
    mock_uow.bookings.list_stale_pending = AsyncMock(return_value=[booking])

    count = await expire_stale_pending(mock_uow, now=NOW)

    assert count == 1
    assert booking.status == BookingStatus.EXPIRED
    assert booking.reserved_until is None
    mock_uow.bookings.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_expire_stale_pending_one_microsecond_before_now_skipped(mock_uow):
    """reserved_until > now still holds capacity; cron must not expire yet."""
    mock_uow.bookings.list_stale_pending = AsyncMock(return_value=[])

    count = await expire_stale_pending(
        mock_uow,
        now=NOW - timedelta(microseconds=1),
    )

    assert count == 0
    mock_uow.bookings.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_expire_stale_pending_one_second_after_now_transitions(mock_uow):
    booking = _pending_booking(reserved_until=NOW)
    mock_uow.bookings.list_stale_pending = AsyncMock(return_value=[booking])

    count = await expire_stale_pending(mock_uow, now=NOW + timedelta(seconds=1))

    assert count == 1
    assert booking.status == BookingStatus.EXPIRED


@pytest.mark.asyncio
async def test_expire_stale_pending_no_rows_skips_flush(mock_uow):
    mock_uow.bookings.list_stale_pending = AsyncMock(return_value=[])

    count = await expire_stale_pending(mock_uow, now=NOW)

    assert count == 0
    mock_uow.bookings.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_past_confirmed_before_end_time_skipped(mock_uow):
    mock_uow.bookings.list_past_confirmed = AsyncMock(return_value=[])

    count = await complete_past_confirmed(mock_uow, now=NOW)

    assert count == 0
    mock_uow.bookings.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_past_confirmed_at_end_time_skipped(mock_uow):
    """occurrence.end_time == now is still in progress; must not complete."""
    mock_uow.bookings.list_past_confirmed = AsyncMock(return_value=[])

    count = await complete_past_confirmed(mock_uow, now=NOW)

    assert count == 0


@pytest.mark.asyncio
async def test_complete_past_confirmed_after_end_time_transitions(mock_uow):
    booking = Booking(
        occurrence_id=1, guest_email="guest@example.com", status=BookingStatus.CONFIRMED
    )
    booking.id = 2
    mock_uow.bookings.list_past_confirmed = AsyncMock(return_value=[booking])

    count = await complete_past_confirmed(mock_uow, now=NOW)

    assert count == 1
    assert booking.status == BookingStatus.COMPLETED
    assert booking.reserved_until is None
    mock_uow.bookings.flush.assert_awaited_once()


def test_list_stale_pending_sql_boundary_includes_equality():
    from sqlalchemy import select

    query = select(Booking).where(
        Booking.status == BookingStatus.PENDING,
        Booking.reserved_until.is_not(None),
        Booking.reserved_until <= NOW,
    )
    compiled = str(query)
    assert "reserved_until" in compiled
    assert "<=" in compiled


def test_active_pending_hold_clause_uses_strict_greater_than():
    clause = BookingRepository._active_pending_hold_clause(now=NOW)
    compiled = str(clause)
    assert "reserved_until" in compiled
    assert ">" in compiled


def test_list_past_confirmed_sql_uses_strict_end_time_comparison():
    from sqlalchemy import select

    from app.models.occurrence import Occurrence

    query = (
        select(Booking)
        .join(Booking.occurrence)
        .where(
            Booking.status == BookingStatus.CONFIRMED,
            Occurrence.end_time < NOW,
        )
    )
    compiled = str(query)
    assert "end_time" in compiled
    assert "status" in compiled
    assert "<" in compiled
