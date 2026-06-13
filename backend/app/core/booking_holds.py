"""
Pending booking hold window helpers.

WHY: pending bookings must reserve capacity only for BOOKING_HOLD_MINUTES,
then release seats without a background job (capacity queries filter by reserved_until).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.models.booking import BookingStatus


def _ensure_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def get_booking_reserved_until(*, now: datetime | None = None) -> datetime:
    """Return UTC-aware timestamp when a new pending hold should expire."""
    now_utc = _ensure_utc_aware(now or datetime.now(UTC))
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
    return _ensure_utc_aware(reserved_until) > _ensure_utc_aware(now)
