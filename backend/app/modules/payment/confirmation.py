"""Payment confirmation after successful Stripe checkout."""

from __future__ import annotations

import structlog

from app.core.datetime_utils import utc_now
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.booking import BookingStatus
from app.models.occurrence import Occurrence
from app.models.order import OrderStatus
from app.modules.payment.capacity import (
    PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW,
    apply_in_memory_confirm_to_capacity_state,
    handle_overbooked_payment,
    would_exceed_occurrence_capacity,
    would_exceed_occurrence_capacity_in_memory,
)

PAYMENT_STATUS_SUCCEEDED = "succeeded"
PAYMENT_CONFIRMABLE_BOOKING_STATUSES = frozenset(
    {
        BookingStatus.PENDING,
        BookingStatus.EXPIRED,
    }
)
logger = structlog.get_logger(__name__)


async def confirm_booking_after_payment(
    uow: UnitOfWork,
    booking_id: int,
    *,
    payment_intent_id: str | None = None,
) -> bool:
    """
    Confirm booking after successful payment (webhook).

    Idempotent: if already CONFIRMED — no-op, returns True.
    On overbooking: cancelled + payment_status=overbooked_manual_review (owner resolves).
    Returns True if processed (or already was), False if booking not found.
    """
    booking = await uow.bookings.get_by_id(booking_id)
    if booking is None:
        return False
    if booking.status == BookingStatus.CONFIRMED:
        return True
    if (
        booking.status == BookingStatus.CANCELLED
        and booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    ):
        await uow.payments.mark_booking_manual_review(
            booking_id=booking.id,
            payment_intent_id=payment_intent_id,
        )
        return True
    if booking.status not in PAYMENT_CONFIRMABLE_BOOKING_STATUSES:
        await uow.payments.mark_booking_manual_review(
            booking_id=booking.id,
            payment_intent_id=payment_intent_id,
        )
        return True

    now_utc = utc_now()
    occurrence = await uow.occurrences.get_by_id_for_update(booking.occurrence_id)
    if occurrence is None:
        return False

    if await would_exceed_occurrence_capacity(
        uow,
        occurrence=occurrence,
        booking_id=booking.id,
        now=now_utc,
    ):
        await handle_overbooked_payment(uow, booking, payment_intent_id=payment_intent_id)
        return True

    booking.status = BookingStatus.CONFIRMED
    booking.payment_status = PAYMENT_STATUS_SUCCEEDED
    booking.reserved_until = None
    booking.access_token = None
    if payment_intent_id:
        booking.payment_intent_id = payment_intent_id
    await uow.bookings.flush()
    log_domain_event(
        logger,
        "payment_confirmed",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        payment_intent_id=payment_intent_id,
        payment_status=booking.payment_status,
    )
    return True


async def confirm_order_after_payment(
    uow: UnitOfWork,
    order_id: int,
    *,
    payment_intent_id: str | None = None,
) -> bool:
    """
    Confirm order and all linked bookings after successful payment (webhook).

    Idempotent: if order already PAID — no-op, returns True.
    Per-occurrence capacity recheck; overbooked bookings go to manual owner review.
    Returns True if processed (or already was), False if order not found.
    """
    order = await uow.orders.get_by_id(order_id)
    if order is None:
        return False
    if order.status == OrderStatus.PAID:
        return True
    if order.status in {OrderStatus.CANCELLED, OrderStatus.REFUNDED}:
        order.status = OrderStatus.MANUAL_REVIEW
        await uow.payments.mark_order_manual_review(
            order_id=order.id,
            payment_intent_id=payment_intent_id,
        )
        await uow.orders.flush()
        return True

    now_utc = utc_now()
    bookings = await uow.bookings.list_(order_id=order_id, limit=1000)

    occurrence_ids_to_lock = sorted(
        {
            b.occurrence_id
            for b in bookings
            if b.status in PAYMENT_CONFIRMABLE_BOOKING_STATUSES
        }
    )
    occurrences_by_id: dict[int, Occurrence] = {}
    # WHY: global lock order to prevent deadlocks (matches occurrence_repo FOR UPDATE order)
    for occurrence_id in occurrence_ids_to_lock:
        occurrence = await uow.occurrences.get_by_id_for_update(occurrence_id)
        if occurrence is not None:
            occurrences_by_id[occurrence_id] = occurrence

    counts_map = await uow.bookings.get_confirmed_pending_counts_by_occurrence_ids(
        occurrence_ids_to_lock,
        now=now_utc,
    )
    capacity_state = {
        occurrence_id: counts_map.get(occurrence_id, (0, 0))
        for occurrence_id in occurrence_ids_to_lock
    }

    order.access_token = None
    confirmed_count = 0
    manual_review_count = 0
    for booking in bookings:
        if booking.status == BookingStatus.CONFIRMED:
            confirmed_count += 1
            continue
        if (
            booking.status == BookingStatus.CANCELLED
            and booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
        ):
            manual_review_count += 1
            continue
        if booking.status not in PAYMENT_CONFIRMABLE_BOOKING_STATUSES:
            manual_review_count += 1
            continue

        occurrence = occurrences_by_id.get(booking.occurrence_id)
        if occurrence is None:
            booking.status = BookingStatus.CANCELLED
            booking.payment_status = PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
            booking.reserved_until = None
            booking.access_token = None
            if payment_intent_id:
                booking.payment_intent_id = payment_intent_id
            manual_review_count += 1
            continue

        if would_exceed_occurrence_capacity_in_memory(
            occurrence=occurrence,
            booking=booking,
            capacity_state=capacity_state,
            now=now_utc,
        ):
            await handle_overbooked_payment(uow, booking, payment_intent_id=payment_intent_id)
            manual_review_count += 1
            continue

        booking.status = BookingStatus.CONFIRMED
        booking.payment_status = PAYMENT_STATUS_SUCCEEDED
        booking.reserved_until = None
        booking.access_token = None
        if payment_intent_id:
            booking.payment_intent_id = payment_intent_id
        apply_in_memory_confirm_to_capacity_state(
            occurrence_id=occurrence.id,
            booking=booking,
            capacity_state=capacity_state,
            now=now_utc,
        )
        confirmed_count += 1

    if manual_review_count > 0 or confirmed_count == 0:
        order.status = OrderStatus.MANUAL_REVIEW
        await uow.payments.mark_order_manual_review(
            order_id=order.id,
            payment_intent_id=payment_intent_id,
        )
    else:
        order.status = OrderStatus.PAID
    await uow.orders.flush()
    log_domain_event(
        logger,
        "payment_confirmed",
        order_id=order.id,
        confirmed_count=confirmed_count,
        manual_review_count=manual_review_count,
        payment_intent_id=payment_intent_id,
        order_status=order.status,
    )
    return True
