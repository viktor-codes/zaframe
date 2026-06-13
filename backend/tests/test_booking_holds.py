"""
Unit tests for pending booking hold helpers and repository capacity counting.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.booking_holds import get_booking_reserved_until, is_active_pending_hold
from app.models.booking import BookingStatus
from app.repositories.booking_repo import BookingRepository


def test_get_booking_reserved_until_uses_config_window():
    now = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)
    reserved_until = get_booking_reserved_until(now=now)
    assert reserved_until == now + timedelta(minutes=15)


@pytest.mark.parametrize(
    ("status", "reserved_until", "now", "expected"),
    [
        (
            BookingStatus.PENDING,
            datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
            datetime(2026, 6, 13, 12, 0, tzinfo=UTC),
            True,
        ),
        (
            BookingStatus.PENDING,
            datetime(2026, 6, 13, 11, 59, tzinfo=UTC),
            datetime(2026, 6, 13, 12, 0, tzinfo=UTC),
            False,
        ),
        (BookingStatus.PENDING, None, datetime(2026, 6, 13, 12, 0, tzinfo=UTC), False),
        (
            BookingStatus.CONFIRMED,
            datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
            datetime(2026, 6, 13, 12, 0, tzinfo=UTC),
            False,
        ),
    ],
)
def test_is_active_pending_hold(status, reserved_until, now, expected):
    assert (
        is_active_pending_hold(status=status, reserved_until=reserved_until, now=now)
        is expected
    )


def test_active_pending_hold_clause_sql_includes_expiry_filter():
    now = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)
    clause = BookingRepository._active_pending_hold_clause(now=now)
    compiled = str(clause)
    assert "reserved_until" in compiled
    assert "status" in compiled


@pytest.mark.asyncio
async def test_count_pending_by_slot_uses_active_hold_filter():
    session = MagicMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=2))
    )
    repo = BookingRepository(session)
    now = datetime(2026, 6, 13, 12, 0, tzinfo=UTC)

    count = await repo.count_pending_by_slot(42, now=now)

    assert count == 2
    session.execute.assert_awaited_once()
    query = session.execute.await_args.args[0]
    compiled = str(query)
    assert "reserved_until" in compiled
    assert "bookings.status" in compiled
