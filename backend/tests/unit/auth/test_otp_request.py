"""Unit tests for OTP request commit-before-send flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.modules.auth.otp import request_otp


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.users.get_by_email_including_deleted = AsyncMock(return_value=None)
    uow.otp_codes.count_recent_requests = AsyncMock(return_value=0)
    uow.otp_codes.invalidate_active_for_email = AsyncMock()
    uow.otp_codes.add = AsyncMock()
    return uow


@pytest.mark.asyncio
async def test_request_otp_commits_before_sending_email(mock_uow: MagicMock) -> None:
    """OTP row is committed before Resend is called."""
    call_order: list[str] = []

    async def track_commit() -> None:
        call_order.append("commit")

    async def track_send(email: str, code: str) -> bool:
        call_order.append("send")
        assert email == "user@example.com"
        assert len(code) >= 4
        return True

    mock_uow.commit = AsyncMock(side_effect=track_commit)

    with (
        patch("app.modules.auth.otp.send_otp_email", side_effect=track_send),
        patch("app.modules.auth.otp.generate_otp_code", return_value="123456"),
        patch("app.modules.auth.otp.hash_otp_code", return_value="hashed"),
        patch("app.modules.auth.otp.get_otp_expires_at", return_value=MagicMock()),
    ):
        await request_otp(mock_uow, "user@example.com", "User")

    assert call_order == ["commit", "send"]
    mock_uow.otp_codes.add.assert_awaited_once()
    assert mock_uow.commit.await_count == 1


@pytest.mark.asyncio
async def test_request_otp_invalidates_after_delivery_failure(mock_uow: MagicMock) -> None:
    """Failed delivery invalidates the committed OTP and returns 503."""
    with patch("app.modules.auth.otp.send_otp_email", AsyncMock(return_value=False)):
        with pytest.raises(ServiceUnavailableError, match="could not be sent"):
            await request_otp(mock_uow, "user@example.com", "User")

    assert mock_uow.otp_codes.invalidate_active_for_email.await_count == 2
    assert mock_uow.commit.await_count == 2


@pytest.mark.asyncio
async def test_request_otp_rate_limited_skips_email(mock_uow: MagicMock) -> None:
    mock_uow.otp_codes.count_recent_requests = AsyncMock(return_value=100)

    with (
        patch("app.modules.auth.otp.settings.OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR", 5),
        patch("app.modules.auth.otp.send_otp_email") as mock_send,
        pytest.raises(ValidationError, match="Too many verification codes"),
    ):
        await request_otp(mock_uow, "user@example.com", "User")

    mock_send.assert_not_called()
    mock_uow.otp_codes.add.assert_not_called()
    mock_uow.commit.assert_not_called()
