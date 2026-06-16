"""Booking lifecycle transitions (expire holds, complete past sessions)."""

from __future__ import annotations

from datetime import datetime

from app.core.datetime_utils import utc_now
from app.core.uow import UnitOfWork
from app.models.booking import BookingStatus


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
    for booking in bookings:
        booking.status = BookingStatus.EXPIRED
        booking.reserved_until = None
    if bookings:
        await uow.bookings.flush()
    return len(bookings)


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
    return len(bookings)
