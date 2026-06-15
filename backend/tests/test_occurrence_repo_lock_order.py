"""
Unit tests: FOR UPDATE queries on occurrences use ORDER BY occurrences.id ASC.

CRIT-2 — unified deterministic lock order to prevent deadlocks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.occurrence_repo import OccurrenceRepository


def _empty_execute_result() -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    return result


@pytest.mark.asyncio
async def test_list_by_service_active_for_update_orders_by_occurrence_id() -> None:
    session = MagicMock()
    session.execute = AsyncMock(return_value=_empty_execute_result())
    repo = OccurrenceRepository(session)

    await repo.list_by_service_active_for_update(service_id=42)

    query = session.execute.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "FOR UPDATE" in compiled.upper()
    assert "occurrences.id" in compiled
    assert "ORDER BY occurrences.id ASC" in compiled
    assert "start_time" not in compiled.split("ORDER BY")[-1]


@pytest.mark.asyncio
async def test_list_active_future_by_service_for_update_orders_by_occurrence_id() -> None:
    session = MagicMock()
    session.execute = AsyncMock(return_value=_empty_execute_result())
    repo = OccurrenceRepository(session)
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)

    await repo.list_active_future_by_service_for_update(service_id=7, now=now)

    query = session.execute.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "FOR UPDATE" in compiled.upper()
    assert "occurrences.id" in compiled
    assert "ORDER BY occurrences.id ASC" in compiled
    assert "start_time" not in compiled.split("ORDER BY")[-1]
