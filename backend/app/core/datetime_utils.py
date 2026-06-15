"""
Date/time utilities — ADR-001: studio local wall-clock + UTC instants.

All instants are timezone-aware UTC in Python and TIMESTAMPTZ in PostgreSQL.
ScheduleTemplate templates use date + time in the studio IANA timezone.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.exceptions import ValidationError


def utc_now() -> datetime:
    """Current instant as timezone-aware UTC."""
    return datetime.now(UTC)


def validate_iana_timezone(tz_name: str) -> str:
    """Validate IANA timezone identifier; raise ValidationError if unknown."""
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError(f"Invalid IANA timezone: {tz_name}") from exc
    return tz_name


def ensure_utc(dt: datetime) -> datetime:
    """
    Normalize a datetime to timezone-aware UTC.

    Raises ValidationError when the input is naive (no tzinfo).
    """
    if dt.tzinfo is None:
        raise ValidationError(
            "Datetime must include timezone (use ISO 8601 with Z or offset)",
        )
    return dt.astimezone(UTC)


def studio_local_to_utc(d: date, t: time, tz_name: str) -> datetime:
    """
    Combine studio-local calendar date and wall-clock time into a UTC instant.

    Raises ValidationError on invalid timezone or ambiguous/non-existent local times (DST).
    """
    validate_iana_timezone(tz_name)
    tz = ZoneInfo(tz_name)
    try:
        local_dt = datetime.combine(d, t, tzinfo=tz)
    except (ValueError, OSError) as exc:
        raise ValidationError(
            f"Invalid local date/time in timezone {tz_name}: {d} {t}",
        ) from exc
    return local_dt.astimezone(UTC)


def studio_local_date_now(tz_name: str) -> date:
    """Today's calendar date in the studio timezone."""
    validate_iana_timezone(tz_name)
    return utc_now().astimezone(ZoneInfo(tz_name)).date()
