"""Unit tests for booking create idempotency fingerprinting."""

from __future__ import annotations

from app.modules.booking.idempotency import fingerprint_booking_create
from app.modules.booking.order.schemas import CourseBookingCreate
from app.modules.booking.schemas import BookingCreate


def test_fingerprint_stable_for_same_payload() -> None:
    schema = BookingCreate(
        occurrence_id=1,
        guest_name="Ada",
        guest_email="ada@example.com",
        guest_phone=None,
    )
    assert fingerprint_booking_create(schema, user_id=None) == fingerprint_booking_create(
        schema, user_id=None
    )


def test_fingerprint_differs_when_email_changes() -> None:
    a = BookingCreate(
        occurrence_id=1,
        guest_name="Ada",
        guest_email="ada@example.com",
        guest_phone=None,
    )
    b = BookingCreate(
        occurrence_id=1,
        guest_name="Ada",
        guest_email="other@example.com",
        guest_phone=None,
    )
    assert fingerprint_booking_create(a, user_id=None) != fingerprint_booking_create(
        b, user_id=None
    )


def test_course_fingerprint_includes_service_id() -> None:
    a = CourseBookingCreate(
        service_id=1,
        guest_name="Ada",
        guest_email="ada@example.com",
    )
    b = CourseBookingCreate(
        service_id=2,
        guest_name="Ada",
        guest_email="ada@example.com",
    )
    assert fingerprint_booking_create(a, user_id=None) != fingerprint_booking_create(
        b, user_id=None
    )
