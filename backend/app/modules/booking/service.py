"""
Booking write operations: create, cancel, and persistence helpers.

Persist helpers stay here until td-05 extracts booking/persistence.py.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.access_tokens import generate_resource_access_token
from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus, BookingType
from app.modules.booking.schemas import BookingCreate

DUPLICATE_BOOKING_MESSAGE = "You already have a booking for this session"

_ACTIVE_BOOKING_UNIQUE_INDEX_NAMES = frozenset(
    {
        "uq_bookings_occurrence_guest_email_active",
        "uq_bookings_occurrence_user_id_active",
    }
)


def _is_active_booking_unique_violation(exc: IntegrityError) -> bool:
    """True when PostgreSQL rejected a duplicate active booking insert."""
    orig = exc.orig
    if orig is None:
        return False
    constraint_name = getattr(orig, "constraint_name", None)
    if constraint_name in _ACTIVE_BOOKING_UNIQUE_INDEX_NAMES:
        return True
    message = str(orig)
    return any(name in message for name in _ACTIVE_BOOKING_UNIQUE_INDEX_NAMES)


async def _ensure_no_active_booking_for_guest(
    uow: UnitOfWork,
    *,
    occurrence_id: int,
    guest_email: str,
    user_id: int | None = None,
) -> None:
    """Raise ValidationError when guest already has a non-cancelled booking on the occurrence."""
    if user_id is not None:
        existing_by_user = await uow.bookings.get_active_by_occurrence_and_user_id(
            occurrence_id, user_id
        )
        if existing_by_user is not None:
            raise ValidationError(DUPLICATE_BOOKING_MESSAGE)

    existing = await uow.bookings.get_active_by_occurrence_and_guest_email(
        occurrence_id, guest_email
    )
    if existing is not None:
        raise ValidationError(DUPLICATE_BOOKING_MESSAGE)


async def _persist_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """Insert booking; map unique-index races to ConflictError."""
    try:
        return await uow.bookings.add(booking)
    except IntegrityError as exc:
        if _is_active_booking_unique_violation(exc):
            raise ConflictError(DUPLICATE_BOOKING_MESSAGE) from exc
        raise


async def _persist_bookings(uow: UnitOfWork, bookings: list[Booking]) -> list[Booking]:
    """Insert multiple bookings; map unique-index races to ConflictError."""
    try:
        return await uow.bookings.add_all(bookings)
    except IntegrityError as exc:
        if _is_active_booking_unique_violation(exc):
            raise ConflictError(DUPLICATE_BOOKING_MESSAGE) from exc
        raise


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

    await _ensure_no_active_booking_for_guest(
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
    return await _persist_booking(uow, booking)


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
