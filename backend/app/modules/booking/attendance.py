"""Booking attendance: check-in and no-show (studio staff / assigned instructor)."""

from __future__ import annotations

import structlog

from app.core.datetime_utils import utc_now
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus
from app.models.studio_member import StudioMemberRole
from app.models.user import User

logger = structlog.get_logger(__name__)


async def _get_attendance_booking_or_raise(uow: UnitOfWork, booking_id: int) -> Booking:
    booking = await uow.bookings.get_by_id_for_update_with_occurrence_and_studio(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


async def _ensure_can_manage_attendance(
    uow: UnitOfWork,
    *,
    booking: Booking,
    user: User,
) -> None:
    studio = booking.occurrence.studio
    membership = await uow.studio_members.get_by_studio_and_user(
        studio_id=studio.id,
        user_id=user.id,
    )
    role = membership.role if membership is not None else None
    if studio.owner_id == user.id:
        role = StudioMemberRole.OWNER.value

    if role in (StudioMemberRole.OWNER.value, StudioMemberRole.MANAGER.value):
        return
    if (
        role == StudioMemberRole.INSTRUCTOR.value
        and membership is not None
        and booking.occurrence.instructor_id == membership.id
    ):
        return
    log_domain_event(
        logger,
        "permission_denied",
        level="warning",
        user_id=user.id,
        studio_id=studio.id,
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        permission="check_in_booking",
    )
    raise ForbiddenError("Access denied for this booking")


def _ensure_attendance_action_allowed(booking: Booking) -> None:
    if booking.status in (BookingStatus.CANCELLED, BookingStatus.EXPIRED):
        raise ValidationError(f"Cannot update attendance for a {booking.status} booking")
    if booking.status == BookingStatus.PENDING:
        raise ValidationError("Cannot update attendance for a pending booking")


async def check_in_booking(
    uow: UnitOfWork,
    *,
    booking_id: int,
    user: User,
) -> Booking:
    """Idempotently mark an attendee as checked in."""
    booking = await _get_attendance_booking_or_raise(uow, booking_id)
    await _ensure_can_manage_attendance(uow, booking=booking, user=user)
    _ensure_attendance_action_allowed(booking)
    if booking.no_show_at is not None or booking.status == BookingStatus.NO_SHOW:
        raise ValidationError("Cannot check in a booking marked as no-show")
    if booking.checked_in_at is not None:
        return booking

    booking.checked_in_at = utc_now()
    booking.no_show_at = None
    booking.status = BookingStatus.COMPLETED
    booking.reserved_until = None
    booking = await uow.bookings.save(booking)
    log_domain_event(
        logger,
        "booking_checked_in",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        user_id=user.id,
    )
    return booking


async def mark_booking_no_show(
    uow: UnitOfWork,
    *,
    booking_id: int,
    user: User,
) -> Booking:
    """Idempotently mark an attendee as no-show."""
    booking = await _get_attendance_booking_or_raise(uow, booking_id)
    await _ensure_can_manage_attendance(uow, booking=booking, user=user)
    _ensure_attendance_action_allowed(booking)
    if booking.checked_in_at is not None:
        raise ValidationError("Cannot mark a checked-in booking as no-show")
    if booking.no_show_at is not None or booking.status == BookingStatus.NO_SHOW:
        return booking

    booking.no_show_at = utc_now()
    booking.status = BookingStatus.NO_SHOW
    booking.reserved_until = None
    booking = await uow.bookings.save(booking)
    log_domain_event(
        logger,
        "booking_no_show",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        user_id=user.id,
    )
    return booking
