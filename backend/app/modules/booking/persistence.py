"""Intra-domain booking write persistence helpers."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking

DUPLICATE_BOOKING_MESSAGE = "You already have a booking for this session"

_ACTIVE_BOOKING_UNIQUE_INDEX_NAMES = frozenset(
    {
        "uq_bookings_occurrence_guest_email_active",
        "uq_bookings_occurrence_user_id_active",
    }
)


def is_active_booking_unique_violation(exc: IntegrityError) -> bool:
    """True when PostgreSQL rejected a duplicate active booking insert."""
    orig = exc.orig
    if orig is None:
        return False
    constraint_name = getattr(orig, "constraint_name", None)
    if constraint_name in _ACTIVE_BOOKING_UNIQUE_INDEX_NAMES:
        return True
    message = str(orig)
    return any(name in message for name in _ACTIVE_BOOKING_UNIQUE_INDEX_NAMES)


async def ensure_no_active_booking_for_guest(
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


async def persist_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """Insert booking; map unique-index races to ConflictError."""
    try:
        return await uow.bookings.add(booking)
    except IntegrityError as exc:
        if is_active_booking_unique_violation(exc):
            raise ConflictError(DUPLICATE_BOOKING_MESSAGE) from exc
        raise


async def persist_bookings(uow: UnitOfWork, bookings: list[Booking]) -> list[Booking]:
    """Insert multiple bookings; map unique-index races to ConflictError."""
    try:
        return await uow.bookings.add_all(bookings)
    except IntegrityError as exc:
        if is_active_booking_unique_violation(exc):
            raise ConflictError(DUPLICATE_BOOKING_MESSAGE) from exc
        raise
