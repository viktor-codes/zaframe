"""
Booking write operations: create and cancel.
"""

from __future__ import annotations

from datetime import timedelta

import structlog

from app.core.access_tokens import generate_resource_access_token
from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.studio_member import StudioMemberRole
from app.models.user import User
from app.modules.booking.persistence import (
    ensure_no_active_booking_for_guest,
    persist_booking,
)
from app.modules.booking.policies import is_own_booking
from app.modules.booking.schemas import BookingCreate
from app.modules.catalog.studio import has_studio_permission

logger = structlog.get_logger(__name__)


async def create_booking(
    uow: UnitOfWork,
    schema: BookingCreate,
    *,
    user: User | None = None,
) -> Booking:
    """
    Create a booking (guest or authenticated).

    Validates:
    - occurrence exists and is active
    - occurrence is in the future
    - seats are available

    When ``user`` is provided (Bearer on POST /bookings), ``user_id`` is set
    immediately so the booking appears in ``GET /bookings/my``. Guests without
    a token still get ``user_id=None`` until OTP attach.
    """
    occurrence = await uow.occurrences.get_by_id_for_update_with_service(schema.occurrence_id)
    if occurrence is None:
        raise NotFoundError("Occurrence not found")
    if not occurrence.is_bookable() or not occurrence.service.is_bookable():
        raise ValidationError("Occurrence is not available for booking")

    now_utc = utc_now()
    occurrence_start = ensure_utc(occurrence.start_time)
    if occurrence_start <= now_utc:
        raise ValidationError("Cannot book an occurrence in the past")

    confirmed_count = await uow.bookings.count_confirmed_by_occurrence(occurrence.id)
    pending_count = await uow.bookings.count_pending_by_occurrence(occurrence.id, now=now_utc)
    if confirmed_count + pending_count >= occurrence.max_capacity:
        raise ValidationError("No seats available")

    user_id = user.id if user is not None else None
    await ensure_no_active_booking_for_guest(
        uow,
        occurrence_id=schema.occurrence_id,
        guest_email=schema.guest_email,
        user_id=user_id,
    )

    booking = Booking(
        occurrence_id=schema.occurrence_id,
        user_id=user_id,
        guest_name=schema.guest_name,
        guest_email=schema.guest_email,
        guest_phone=schema.guest_phone,
        status=BookingStatus.PENDING,
        reserved_until=get_booking_reserved_until(now=now_utc),
        booking_type=getattr(schema, "booking_type", BookingType.SINGLE),
        service_id=getattr(schema, "service_id", None),
        access_token=generate_resource_access_token(),
    )
    booking = await persist_booking(uow, booking)
    log_domain_event(
        logger,
        "booking_created",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        service_id=booking.service_id,
        order_id=booking.order_id,
        booking_type=booking.booking_type,
        user_id=user_id,
    )
    return booking


async def cancel_booking(uow: UnitOfWork, booking: Booking, *, user: User) -> Booking:
    """
    Cancel a booking.

    Only pending or confirmed bookings can be cancelled.
    Caller must own the booking (subject to cancel_before_hours) or hold
    manage_bookings on the studio. view_bookings alone is not enough.
    """
    if booking.status == BookingStatus.CANCELLED:
        raise ValidationError("Booking is already cancelled")
    if booking.status in (BookingStatus.EXPIRED, BookingStatus.COMPLETED, BookingStatus.NO_SHOW):
        raise ValidationError(f"Cannot cancel a {booking.status} booking")

    now_utc = utc_now()
    if is_own_booking(booking, user):
        occurrence_start = ensure_utc(booking.occurrence.start_time)
        cutoff = occurrence_start - timedelta(hours=booking.occurrence.studio.cancel_before_hours)
        can_bypass_cutoff = await has_studio_permission(
            uow,
            studio=booking.occurrence.studio,
            user=user,
            permission="manage_bookings",
        )
        if not can_bypass_cutoff and now_utc >= cutoff:
            raise ForbiddenError("Cancellation cutoff has passed")
    else:
        can_manage = await has_studio_permission(
            uow,
            studio=booking.occurrence.studio,
            user=user,
            permission="manage_bookings",
        )
        if not can_manage:
            raise ForbiddenError("Access denied for this studio")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now_utc
    booking.reserved_until = None
    booking = await uow.bookings.save(booking)
    log_domain_event(
        logger,
        "booking_cancelled",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        user_id=user.id,
    )
    return booking


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
