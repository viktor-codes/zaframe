"""Tests for timezone-aware datetime fields in output schemas (MID-2)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp

from app.modules.booking.schemas import BookingSelfResponse
from app.modules.catalog.occurrence import OccurrenceCreate, OccurrenceResponse

_ISO_OFFSET_SUFFIX = re.compile(r"(Z|[+-]\d{2}:\d{2})$")


def _assert_iso_has_offset(value: str) -> None:
    assert _ISO_OFFSET_SUFFIX.search(value), f"Expected ISO 8601 with offset, got {value!r}"


def test_occurrence_response_serializes_utc_with_offset():
    """OccurrenceResponse must serialize instants with Z or numeric offset."""
    start = datetime(2026, 6, 15, 18, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    end = start + timedelta(hours=1)
    created = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)

    occurrence = SimpleNamespace(
        id=1,
        studio_id=2,
        status="active",
        start_time=start,
        end_time=end,
        title="Evening Class",
        description=None,
        max_capacity=10,
        price_cents=1500,
        course_price_cents=None,
        created_at=created,
        updated_at=created,
        instructor_id=None,
        instructor=None,
    )

    payload = OccurrenceResponse.model_validate(occurrence).model_dump(mode="json")

    _assert_iso_has_offset(payload["start_time"])
    _assert_iso_has_offset(payload["end_time"])
    _assert_iso_has_offset(payload["created_at"])
    _assert_iso_has_offset(payload["updated_at"])
    assert payload["start_time"].endswith("Z")
    assert payload["end_time"].endswith("Z")


def test_booking_response_reserved_until_is_aware():
    """Booking response must serialize reserved_until as timezone-aware ISO 8601."""
    reserved_until = datetime(2026, 6, 15, 12, 15, tzinfo=UTC)
    booking = SimpleNamespace(
        occurrence_id=10,
        id=1,
        user_id=None,
        guest_name="Guest User",
        guest_email="guest@example.com",
        guest_phone="+111111111",
        status="pending",
        reserved_until=reserved_until,
        payment_status="unpaid",
        created_at=reserved_until,
        updated_at=reserved_until,
        cancelled_at=None,
        checked_in_at=None,
        no_show_at=None,
    )

    payload = BookingSelfResponse.model_validate(booking).model_dump(mode="json")

    _assert_iso_has_offset(payload["reserved_until"])
    _assert_iso_has_offset(payload["created_at"])
    _assert_iso_has_offset(payload["updated_at"])


def test_create_occurrence_schema_rejects_naive_datetime():
    """OccurrenceCreate must reject naive datetimes at the schema boundary."""
    with pytest.raises(ValueError, match="timezone"):
        OccurrenceCreate(
            studio_id=1,
            start_time=datetime(2026, 6, 15, 18, 0),
            end_time=datetime(2026, 6, 15, 19, 0),
            title="Morning Class",
        )


@pytest.mark.integration
async def test_create_occurrence_rejects_naive_datetime(client: AsyncClient):
    """POST /occurrences with naive datetimes must return 422."""
    data = await authenticate_via_otp(client, email="naive-dt-owner@example.com", name="Owner")
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Naive Datetime Studio",
            "description": "For naive datetime rejection test",
            "email": "naive-dt-studio@example.com",
            "address": "Test street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    response = await client.post(
        "/api/v1/occurrences",
        json={
            "start_time": "2026-06-15T18:00:00",
            "end_time": "2026-06-15T19:00:00",
            "title": "Morning Class",
            "description": "Test slot",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": None,
        },
        headers=headers,
    )

    assert response.status_code == 422
