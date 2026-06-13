"""
Pending booking hold window helpers.

WHY: pending bookings must reserve capacity only for BOOKING_HOLD_MINUTES,
then release seats without a background job (capacity queries filter by reserved_until).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.config import settings
from app.core.datetime_utils import ensure_utc, utc_now
from app.models.booking import BookingStatus


def get_booking_reserved_until(*, now: datetime | None = None) -> datetime:
    """Return UTC-aware timestamp when a new pending hold should expire."""
    now_utc = ensure_utc(now) if now is not None else utc_now()
    return now_utc + timedelta(minutes=settings.BOOKING_HOLD_MINUTES)


def is_active_pending_hold(
    *,
    status: str,
    reserved_until: datetime | None,
    now: datetime,
) -> bool:
    """
    True when a pending booking still reserves slot capacity.

    Legacy rows with reserved_until=NULL are treated as expired holds.
    """
    if status != BookingStatus.PENDING:
        return False
    if reserved_until is None:
        return False
    return ensure_utc(reserved_until) > ensure_utc(now)
