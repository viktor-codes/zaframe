"""
Unit tests for OTP email logging — no OTP codes or plain emails in production logs.
"""

import logging
from unittest.mock import patch

import pytest
import structlog
from structlog.testing import LogCapture

from app.integrations.email.service import send_otp_email


@pytest.fixture
def log_capture():
    """Capture structlog events for assertions."""
    cap = LogCapture()
    structlog.configure(
        processors=[cap],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    yield cap
    structlog.reset_defaults()


@pytest.mark.asyncio
async def test_no_otp_or_plain_email_in_logs_when_debug_false(log_capture):
    """Production without Resend must not leak OTP or full email in logs."""
    email = "john@domain.com"
    code = "123456"

    with (
        patch("app.integrations.email.service.settings.RESEND_API_KEY", None),
        patch("app.integrations.email.service.settings.DEBUG", False),
    ):
        result = await send_otp_email(email, code)

    assert result is False
    assert len(log_capture.entries) == 1
    entry = log_capture.entries[0]
    assert entry["event"] == "otp_provider_not_configured"
    assert "otp_code" not in entry
    assert code not in str(entry)
    assert email not in str(entry)
    assert "john@domain.com" not in str(entry)


@pytest.mark.asyncio
async def test_dev_mode_does_not_log_otp_code_when_debug_true(log_capture):
    """Local DEBUG=True accepts requests without leaking OTP or full email."""
    email = "john@domain.com"
    code = "654321"

    with (
        patch("app.integrations.email.service.settings.RESEND_API_KEY", None),
        patch("app.integrations.email.service.settings.DEBUG", True),
    ):
        result = await send_otp_email(email, code)

    assert result is True
    assert len(log_capture.entries) == 1
    entry = log_capture.entries[0]
    assert entry["event"] == "otp_dev_mode_no_provider"
    assert entry["otp_email_masked"] == "j***@d***.com"
    assert "otp_code" not in entry
    assert code not in str(entry)
    assert email not in str(entry)


@pytest.mark.asyncio
async def test_send_otp_email_uses_configured_sender():
    """Resend payload uses EMAIL_FROM from settings, not a hardcoded sender."""
    sent_payloads: list[dict[str, object]] = []

    def capture_send(payload: dict[str, object]) -> dict[str, str]:
        sent_payloads.append(payload)
        return {"id": "email_123"}

    with (
        patch("app.integrations.email.service.settings.RESEND_API_KEY", "re_test"),
        patch("app.integrations.email.service.settings.EMAIL_FROM", "ZeeFrame <login@example.com>"),
        patch("resend.Emails.send", side_effect=capture_send),
    ):
        result = await send_otp_email("john@domain.com", "123456")

    assert result is True
    assert sent_payloads[0]["from"] == "ZeeFrame <login@example.com>"
