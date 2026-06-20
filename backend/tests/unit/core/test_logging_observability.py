"""Observability contracts for request logging and safe domain events."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest
import structlog
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from structlog.testing import LogCapture

from app.core.middleware.logging_middleware import REQUEST_ID_HEADER, RequestLoggingMiddleware
from app.core.observability import log_domain_event, safe_log_fields
from app.main import unhandled_exception_handler


@pytest.fixture
def log_capture() -> Iterator[LogCapture]:
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


def _app_with_request_logging() -> FastAPI:
    app = FastAPI(debug=False)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    async def ok_response() -> dict[str, str]:
        return {"status": "ok"}

    async def boom_response() -> None:
        raise RuntimeError("database password leaked in exception text")

    app.add_api_route("/ok", ok_response, methods=["GET"])
    app.add_api_route("/boom", boom_response, methods=["GET"])
    return app


@pytest.mark.asyncio
async def test_request_middleware_adds_request_id_and_logs_context(
    log_capture: LogCapture,
) -> None:
    """Every response gets X-Request-ID and request logs share that ID."""
    app = _app_with_request_logging()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ok", headers={REQUEST_ID_HEADER: "frontend-request-1"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "frontend-request-1"
    events = [entry for entry in log_capture.entries if entry["event"] == "request_finished"]
    assert len(events) == 1
    assert events[0]["request_id"] == "frontend-request-1"
    assert events[0]["method"] == "GET"
    assert events[0]["path"] == "/ok"
    assert events[0]["status"] == 200


@pytest.mark.asyncio
async def test_request_middleware_replaces_invalid_client_request_id(
    log_capture: LogCapture,
) -> None:
    """Untrusted request IDs are bounded before they enter logs."""
    app = _app_with_request_logging()
    invalid_request_id = "x" * 300
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ok", headers={REQUEST_ID_HEADER: invalid_request_id})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] != invalid_request_id
    assert len(response.headers[REQUEST_ID_HEADER]) <= 128
    events = [entry for entry in log_capture.entries if entry["event"] == "request_finished"]
    assert events[0]["request_id"] == response.headers[REQUEST_ID_HEADER]


@pytest.mark.asyncio
async def test_unhandled_exception_returns_safe_problem_json_and_logs_request_id(
    log_capture: LogCapture,
) -> None:
    """Unexpected errors expose request_id, not internal exception details."""
    app = _app_with_request_logging()
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/boom", headers={REQUEST_ID_HEADER: "req-error-1"})

    assert response.status_code == 500
    assert response.headers[REQUEST_ID_HEADER] == "req-error-1"
    body = response.json()
    assert body["detail"] == "Internal server error"
    assert body["request_id"] == "req-error-1"
    assert "password" not in str(body).lower()

    request_failed = [entry for entry in log_capture.entries if entry["event"] == "request_failed"]
    assert len(request_failed) == 1
    assert request_failed[0]["request_id"] == "req-error-1"
    unhandled = [entry for entry in log_capture.entries if entry["event"] == "unhandled_exception"]
    assert len(unhandled) == 1
    assert unhandled[0]["request_id"] == "req-error-1"
    assert "password leaked" not in str(unhandled[0]).lower()


def test_safe_log_fields_removes_sensitive_values() -> None:
    """Known token/secret fields are dropped before logging."""
    fields = safe_log_fields(
        {
            "booking_id": 10,
            "access_token": "access-token-value",
            "refresh_token": "refresh-token-value",
            "raw_guest_access_token": "guest-token-value",
            "stripe_webhook_secret": "whsec_secret",
            "otp_code": "123456",
        }
    )

    assert fields == {"booking_id": 10}


def test_domain_event_helper_does_not_emit_sensitive_values(log_capture: LogCapture) -> None:
    """Domain event helper protects auth/payment flows from accidental token fields."""
    logger = structlog.get_logger("tests.observability")
    log_domain_event(
        logger,
        "checkout_session_created",
        booking_id=123,
        access_token="secret-access-token",
        refresh_token="secret-refresh-token",
        checkout_session_id="cs_test_123",
    )

    assert len(log_capture.entries) == 1
    entry = log_capture.entries[0]
    assert entry["event"] == "checkout_session_created"
    assert entry["booking_id"] == 123
    assert entry["checkout_session_id"] == "cs_test_123"
    assert "secret-access-token" not in str(entry)
    assert "secret-refresh-token" not in str(entry)
