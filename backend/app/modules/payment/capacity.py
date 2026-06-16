"""In-memory and SQL capacity checks during payment confirmation."""

from __future__ import annotations

from datetime import datetime

import structlog

from app.core.booking_holds import is_active_pending_hold
from app.core.datetime_utils import utc_now
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence

# WHY: paid but occurrence full — studio owner resolves refund/rebook manually (no auto-refund yet).
PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW = "overbooked_manual_review"

logger = structlog.get_logger(__name__)


async def would_exceed_occurrence_capacity(
    uow: UnitOfWork,
    *,
    occurrence: Occurrence,
    booking_id: int,
    now: datetime,
) -> bool:
    """True when confirming booking_id would push the occurrence past max_capacity."""
    confirmed_count = await uow.bookings.count_confirmed_by_occurrence(occurrence.id)
    pending_count = await uow.bookings.count_pending_by_occurrence(
        occurrence.id,
        now=now,
        exclude_booking_id=booking_id,
    )
    return confirmed_count + pending_count + 1 > occurrence.max_capacity


def _booking_counts_as_active_pending_hold(booking: Booking, *, now: datetime) -> bool:
    return is_active_pending_hold(
        status=booking.status,
        reserved_until=booking.reserved_until,
        now=now,
    )


def would_exceed_occurrence_capacity_in_memory(
    *,
    occurrence: Occurrence,
    booking: Booking,
    capacity_state: dict[int, tuple[int, int]],
    now: datetime,
) -> bool:
    """
    Capacity check using pre-fetched counts plus in-loop confirmations.

    Mirrors per-booking SQL recheck: pending excludes the booking being confirmed;
    capacity_state tracks earlier confirmations in the same order under the same lock.
    """
    confirmed, pending = capacity_state.get(occurrence.id, (0, 0))
    booking_counts_as_pending = _booking_counts_as_active_pending_hold(booking, now=now)
    pending_others = pending - (1 if booking_counts_as_pending else 0)
    return confirmed + pending_others + 1 > occurrence.max_capacity


def apply_in_memory_confirm_to_capacity_state(
    *,
    occurrence_id: int,
    booking: Booking,
    capacity_state: dict[int, tuple[int, int]],
    now: datetime,
) -> None:
    """Update local counters after confirming a booking (before DB flush)."""
    confirmed, pending = capacity_state.get(occurrence_id, (0, 0))
    if _booking_counts_as_active_pending_hold(booking, now=now):
        pending -= 1
    capacity_state[occurrence_id] = (confirmed + 1, pending)


async def handle_overbooked_payment(
    uow: UnitOfWork,
    booking: Booking,
    *,
    payment_intent_id: str | None,
) -> None:
    """Mark paid booking for manual studio-owner resolution; do not confirm the seat."""
    now_utc = utc_now()
    booking.status = BookingStatus.CANCELLED
    booking.payment_status = PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    booking.reserved_until = None
    booking.access_token = None
    booking.cancelled_at = now_utc
    if payment_intent_id:
        booking.payment_intent_id = payment_intent_id
    await uow.bookings.flush()
    logger.warning(
        "payment_confirm_overbooked_manual_review",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        payment_intent_id=payment_intent_id,
    )
