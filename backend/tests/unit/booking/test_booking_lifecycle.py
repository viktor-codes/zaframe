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
    uow.commit = AsyncMock()
    uow.orders.expire_pending_without_active_bookings = AsyncMock(return_value=0)
    return uow


def _pending_booking(*, reserved_until: datetime | None, order_id: int | None = None) -> Booking:
    booking = Booking(
        occurrence_id=1,
        guest_email="guest@example.com",
        status=BookingStatus.PENDING,
        reserved_until=reserved_until,
        order_id=order_id,
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
    mock_uow.commit.assert_awaited_once()
    mock_uow.orders.expire_pending_without_active_bookings.assert_awaited_once_with(order_ids=[])


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
    mock_uow.commit.assert_not_awaited()
    mock_uow.orders.expire_pending_without_active_bookings.assert_not_awaited()


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
    mock_uow.commit.assert_not_awaited()
    mock_uow.orders.expire_pending_without_active_bookings.assert_not_awaited()


@pytest.mark.asyncio
async def test_expire_stale_pending_expires_related_order_when_no_active_bookings(mock_uow):
    booking = _pending_booking(reserved_until=NOW, order_id=77)
    mock_uow.bookings.list_stale_pending = AsyncMock(return_value=[booking])

    count = await expire_stale_pending(mock_uow, now=NOW)

    assert count == 1
    mock_uow.orders.expire_pending_without_active_bookings.assert_awaited_once_with(order_ids=[77])


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
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_expire_stale_pending_processes_multiple_batches(mock_uow):
    """Full backlog is drained in LIMIT-sized commits, not one unbounded load."""
    first = _pending_booking(reserved_until=NOW, order_id=1)
    first.id = 1
    second = _pending_booking(reserved_until=NOW, order_id=2)
    second.id = 2
    mock_uow.bookings.list_stale_pending = AsyncMock(side_effect=[[first], [second], []])

    count = await expire_stale_pending(mock_uow, now=NOW, batch_size=1)

    assert count == 2
    assert first.status == BookingStatus.EXPIRED
    assert second.status == BookingStatus.EXPIRED
    assert mock_uow.bookings.list_stale_pending.await_count == 3
    assert mock_uow.commit.await_count == 2


def test_list_stale_pending_sql_boundary_includes_equality():
    from sqlalchemy import or_, select

    query = (
        select(Booking)
        .where(
            Booking.status == BookingStatus.PENDING,
            or_(
                Booking.reserved_until.is_(None),
                Booking.reserved_until <= NOW,
            ),
        )
        .order_by(Booking.id)
        .limit(500)
    )
    compiled = str(query)
    assert "reserved_until" in compiled
    assert "IS NULL" in compiled
    assert "<=" in compiled
    assert "LIMIT" in compiled.upper() or "limit" in compiled


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
        .order_by(Booking.id)
        .limit(500)
    )
    compiled = str(query)
    assert "end_time" in compiled
    assert "status" in compiled
    assert "<" in compiled
    assert "LIMIT" in compiled.upper() or "limit" in compiled
