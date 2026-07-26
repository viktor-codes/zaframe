"""Unit tests for studio dashboard booking list mapping."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.modules.booking.mapping import map_owner_booking_with_occurrence

_FIXED_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)


def _occurrence(*, occurrence_id: int = 10) -> SimpleNamespace:
    start = _FIXED_NOW + timedelta(days=1)
    return SimpleNamespace(
        id=occurrence_id,
        studio_id=5,
        service_id=7,
        instructor_id=None,
        instructor=None,
        start_time=start,
        end_time=start + timedelta(hours=1),
        title="Morning class",
        description=None,
        max_capacity=8,
        price_cents=1500,
        course_price_cents=None,
        status="scheduled",
        cancelled_at=None,
        cancellation_reason=None,
        created_at=_FIXED_NOW,
        updated_at=_FIXED_NOW,
    )


def _booking(*, booking_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        occurrence_id=10,
        id=booking_id,
        user_id=None,
        guest_name="Guest User",
        guest_email="guest@example.com",
        guest_phone=None,
        status="pending",
        reserved_until=_FIXED_NOW,
        payment_status="unpaid",
        created_at=_FIXED_NOW,
        updated_at=_FIXED_NOW,
        cancelled_at=None,
        checked_in_at=None,
        no_show_at=None,
        occurrence=_occurrence(),
    )


def test_map_owner_booking_with_occurrence_embeds_session():
    mapped = map_owner_booking_with_occurrence(_booking())

    assert mapped.id == 1
    assert mapped.guest_email == "guest@example.com"
    assert mapped.occurrence.id == 10
    assert mapped.occurrence.title == "Morning class"
    assert mapped.occurrence.max_capacity == 8
