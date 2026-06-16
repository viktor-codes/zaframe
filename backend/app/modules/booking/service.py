"""
Booking write operations: create and cancel.
"""

from __future__ import annotations

from app.core.access_tokens import generate_resource_access_token
from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus, BookingType
from app.modules.booking.persistence import (
    ensure_no_active_booking_for_guest,
    persist_booking,
)
from app.modules.booking.schemas import BookingCreate


async def create_booking(uow: UnitOfWork, schema: BookingCreate) -> Booking:
    """
    Create a guest booking.

    Validates:
    - occurrence exists and is active
    - occurrence is in the future
    - seats are available

    user_id is set after OTP verify (attach_guest_bookings).
    """
    occurrence = await uow.occurrences.get_by_id_for_update(schema.occurrence_id)
    if occurrence is None:
        raise NotFoundError("Occurrence not found")
    if not occurrence.is_bookable():
        raise ValidationError("Occurrence is not available for booking")

    now_utc = utc_now()
    occurrence_start = ensure_utc(occurrence.start_time)
    if occurrence_start <= now_utc:
        raise ValidationError("Cannot book an occurrence in the past")

    confirmed_count = await uow.bookings.count_confirmed_by_occurrence(occurrence.id)
    pending_count = await uow.bookings.count_pending_by_occurrence(occurrence.id, now=now_utc)
    if confirmed_count + pending_count >= occurrence.max_capacity:
        raise ValidationError("No seats available")

    await ensure_no_active_booking_for_guest(
        uow,
        occurrence_id=schema.occurrence_id,
        guest_email=schema.guest_email,
    )

    booking = Booking(
        occurrence_id=schema.occurrence_id,
        guest_name=schema.guest_name,
        guest_email=schema.guest_email,
        guest_phone=schema.guest_phone,
        status=BookingStatus.PENDING,
        reserved_until=get_booking_reserved_until(now=now_utc),
        booking_type=getattr(schema, "booking_type", BookingType.SINGLE),
        service_id=getattr(schema, "service_id", None),
        access_token=generate_resource_access_token(),
    )
    return await persist_booking(uow, booking)


async def cancel_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """
    Cancel a booking.

    Only pending or confirmed bookings can be cancelled.
    """
    if booking.status == BookingStatus.CANCELLED:
        raise ValidationError("Booking is already cancelled")
    if booking.status in (BookingStatus.EXPIRED, BookingStatus.COMPLETED):
        raise ValidationError(f"Cannot cancel a {booking.status} booking")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = utc_now()
    booking.reserved_until = None
    return await uow.bookings.save(booking)
