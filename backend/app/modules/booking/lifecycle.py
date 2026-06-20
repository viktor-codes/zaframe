"""Booking lifecycle transitions (expire holds, complete past sessions)."""

from __future__ import annotations

from datetime import datetime

import structlog

from app.core.datetime_utils import utc_now
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.booking import BookingStatus

logger = structlog.get_logger(__name__)


async def expire_stale_pending(
    uow: UnitOfWork,
    *,
    now: datetime | None = None,
) -> int:
    """
    Mark pending bookings with expired reserved_until as EXPIRED.

    Returns the number of bookings transitioned.
    """
    now_utc = now or utc_now()
    bookings = await uow.bookings.list_stale_pending(now=now_utc)
    order_ids = sorted({booking.order_id for booking in bookings if booking.order_id is not None})
    for booking in bookings:
        booking.status = BookingStatus.EXPIRED
        booking.reserved_until = None
    if bookings:
        await uow.bookings.flush()
        await uow.orders.expire_pending_without_active_bookings(order_ids=order_ids)
    expired_count = len(bookings)
    log_domain_event(
        logger,
        "lifecycle_expired_pending_bookings",
        expired_count=expired_count,
        order_count=len(order_ids),
    )
    return expired_count


async def complete_past_confirmed(
    uow: UnitOfWork,
    *,
    now: datetime | None = None,
) -> int:
    """
    Mark confirmed bookings as COMPLETED when their occurrence has ended.

    Uses occurrence.end_time < now (still in progress at exactly end_time).
    Returns the number of bookings transitioned.
    """
    now_utc = now or utc_now()
    bookings = await uow.bookings.list_past_confirmed(now=now_utc)
    for booking in bookings:
        booking.status = BookingStatus.COMPLETED
        booking.reserved_until = None
    if bookings:
        await uow.bookings.flush()
    completed_count = len(bookings)
    log_domain_event(
        logger,
        "lifecycle_completed_past_bookings",
        completed_count=completed_count,
    )
    return completed_count
