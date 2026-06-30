"""Integration tests for the scripts.run_booking_lifecycle entrypoint."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts.run_booking_lifecycle import run_booking_lifecycle


@pytest.mark.asyncio
async def test_run_booking_lifecycle_returns_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entrypoint delegates to lifecycle helpers and returns their counts."""
    mock_uow = MagicMock()
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    expire_mock = AsyncMock(return_value=3)
    complete_mock = AsyncMock(return_value=2)

    monkeypatch.setattr("scripts.run_booking_lifecycle.uow_scope", lambda: mock_context)
    monkeypatch.setattr("scripts.run_booking_lifecycle.expire_stale_pending", expire_mock)
    monkeypatch.setattr("scripts.run_booking_lifecycle.complete_past_confirmed", complete_mock)

    expired_count, completed_count = await run_booking_lifecycle()

    assert expired_count == 3
    assert completed_count == 2
    expire_mock.assert_awaited_once_with(mock_uow)
    complete_mock.assert_awaited_once_with(mock_uow)
