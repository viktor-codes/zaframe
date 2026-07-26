"""Unit tests for occurrence capacity response mapping."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.catalog.occurrence.service import to_occurrence_responses_with_capacity


def _occurrence(*, occurrence_id: int = 1) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=occurrence_id,
        studio_id=10,
        service_id=20,
        instructor_id=None,
        instructor=None,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        title="Morning class",
        description=None,
        max_capacity=8,
        price_cents=1500,
        course_price_cents=None,
        status="scheduled",
        cancelled_at=None,
        cancellation_reason=None,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_to_occurrence_responses_with_capacity_empty_list():
    mock_uow = MagicMock()
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids = AsyncMock()

    result = await to_occurrence_responses_with_capacity(mock_uow, [])

    assert result == []
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids.assert_not_called()


@pytest.mark.asyncio
async def test_to_occurrence_responses_with_capacity_attaches_counts():
    mock_uow = MagicMock()
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids = AsyncMock(
        return_value={1: (2, 1), 2: (0, 0)}
    )
    occurrences = [_occurrence(occurrence_id=1), _occurrence(occurrence_id=2)]

    result = await to_occurrence_responses_with_capacity(mock_uow, occurrences)

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].confirmed_count == 2
    assert result[0].pending_count == 1
    assert result[1].id == 2
    assert result[1].confirmed_count == 0
    assert result[1].pending_count == 0
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids.assert_awaited_once()


@pytest.mark.asyncio
async def test_to_occurrence_responses_with_capacity_defaults_missing_ids():
    mock_uow = MagicMock()
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids = AsyncMock(
        return_value={}
    )

    result = await to_occurrence_responses_with_capacity(
        mock_uow,
        [_occurrence(occurrence_id=99)],
    )

    assert result[0].confirmed_count == 0
    assert result[0].pending_count == 0
