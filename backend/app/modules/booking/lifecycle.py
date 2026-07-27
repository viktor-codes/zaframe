"""Booking lifecycle transitions (expire holds, complete past sessions)."""

from __future__ import annotations

from datetime import datetime

import structlog

from app.core.datetime_utils import utc_now
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.booking import BookingStatus

logger = structlog.get_logger(__name__)

# WHY: unbounded SELECT of all stale rows locks memory/pool under backlog growth.
LIFECYCLE_BATCH_SIZE = 500


async def expire_stale_pending(
    uow: UnitOfWork,
    *,
    now: datetime | None = None,
    batch_size: int = LIFECYCLE_BATCH_SIZE,
) -> int:
    """
    Mark pending bookings with expired reserved_until as EXPIRED.

    Processes rows in batches (commit per batch) so large backlogs do not hold
    one long transaction. Returns the number of bookings transitioned.
    """
    now_utc = now or utc_now()
    expired_count = 0
    while True:
        bookings = await uow.bookings.list_stale_pending(now=now_utc, limit=batch_size)
        if not bookings:
            break
        order_ids = sorted(
            {booking.order_id for booking in bookings if booking.order_id is not None}
        )
        for booking in bookings:
            booking.status = BookingStatus.EXPIRED
            booking.reserved_until = None
        await uow.bookings.flush()
        await uow.orders.expire_pending_without_active_bookings(order_ids=order_ids)
        await uow.commit()
        expired_count += len(bookings)
        if len(bookings) < batch_size:
            break

    log_domain_event(
        logger,
        "lifecycle_expired_pending_bookings",
        expired_count=expired_count,
    )
    return expired_count


async def complete_past_confirmed(
    uow: UnitOfWork,
    *,
    now: datetime | None = None,
    batch_size: int = LIFECYCLE_BATCH_SIZE,
) -> int:
    """
    Mark confirmed bookings as COMPLETED when their occurrence has ended.

    Uses occurrence.end_time < now (still in progress at exactly end_time).
    Processes in batches with a commit per batch. Returns transition count.
    """
    now_utc = now or utc_now()
    completed_count = 0
    while True:
        bookings = await uow.bookings.list_past_confirmed(now=now_utc, limit=batch_size)
        if not bookings:
            break
        for booking in bookings:
            booking.status = BookingStatus.COMPLETED
            booking.reserved_until = None
        await uow.bookings.flush()
        await uow.commit()
        completed_count += len(bookings)
        if len(bookings) < batch_size:
            break

    log_domain_event(
        logger,
        "lifecycle_completed_past_bookings",
        completed_count=completed_count,
    )
    return completed_count
