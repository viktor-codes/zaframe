"""Unit tests for email normalization used by booking uniqueness."""

from __future__ import annotations

from app.core.email_utils import normalize_email
from app.modules.booking.order.schemas import CourseBookingCreate
from app.modules.booking.schemas import BookingCreate


def test_normalize_email_strips_and_lowercases() -> None:
    assert normalize_email("  Ada@Example.COM ") == "ada@example.com"


def test_booking_create_normalizes_guest_email() -> None:
    schema = BookingCreate(
        occurrence_id=1,
        guest_name="Ada",
        guest_email="Ada@Example.COM",
        guest_phone=None,
    )
    assert schema.guest_email == "ada@example.com"


def test_course_booking_create_normalizes_guest_email() -> None:
    schema = CourseBookingCreate(
        service_id=1,
        guest_name="Ada",
        guest_email="Ada@Example.COM",
    )
    assert schema.guest_email == "ada@example.com"
