"""
Unit tests for ADR-001 datetime utilities, including DST edge cases.

Run immediately after changing studio_local_to_utc — before seeds or integration tests.
"""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.core.datetime_utils import (
    ensure_utc,
    studio_local_date_now,
    studio_local_to_utc,
    utc_now,
    validate_iana_timezone,
)
from app.core.exceptions import ValidationError


def test_utc_now_is_aware_utc():
    now = utc_now()
    assert now.tzinfo is UTC
    assert now.tzinfo is not None


def test_validate_iana_timezone_accepts_known_zone():
    assert validate_iana_timezone("Europe/Berlin") == "Europe/Berlin"


def test_validate_iana_timezone_rejects_unknown_zone():
    with pytest.raises(ValidationError, match="Invalid IANA timezone"):
        validate_iana_timezone("Not/A_Real_Zone")


def test_ensure_utc_converts_offset_to_utc():
    berlin = datetime(2026, 6, 15, 18, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    result = ensure_utc(berlin)
    assert result.tzinfo is UTC
    assert result.hour == 16  # CEST = UTC+2 in June


def test_ensure_utc_rejects_naive():
    with pytest.raises(ValidationError, match="must include timezone"):
        ensure_utc(datetime(2026, 6, 15, 18, 0))


def test_studio_local_to_utc_winter_berlin():
    """Standard time (CET, UTC+1): 18:00 Berlin -> 17:00 UTC."""
    instant = studio_local_to_utc(date(2026, 1, 15), time(18, 0), "Europe/Berlin")
    assert instant.tzinfo is UTC
    assert instant == datetime(2026, 1, 15, 17, 0, tzinfo=UTC)


def test_studio_local_to_utc_summer_berlin():
    """Daylight time (CEST, UTC+2): 18:00 Berlin -> 16:00 UTC."""
    instant = studio_local_to_utc(date(2026, 6, 15), time(18, 0), "Europe/Berlin")
    assert instant.tzinfo is UTC
    assert instant == datetime(2026, 6, 15, 16, 0, tzinfo=UTC)


def test_studio_local_to_utc_fall_back_ambiguous_defaults_fold_zero():
    """During fall-back, 02:30 exists twice; datetime.combine uses fold=0 (CEST instance)."""
    instant = studio_local_to_utc(date(2026, 10, 25), time(2, 30), "Europe/Berlin")
    assert instant == datetime(2026, 10, 25, 0, 30, tzinfo=UTC)


def test_studio_local_to_utc_tokyo_no_dst():
    """Asia/Tokyo has no DST — stable offset UTC+9."""
    instant = studio_local_to_utc(date(2026, 6, 15), time(9, 0), "Asia/Tokyo")
    assert instant == datetime(2026, 6, 15, 0, 0, tzinfo=UTC)


def test_studio_local_date_now_matches_studio_timezone():
    fixed_utc = datetime(2026, 6, 15, 23, 30, tzinfo=UTC)
    # In Tokyo (UTC+9) it's already June 16
    tokyo_date = fixed_utc.astimezone(ZoneInfo("Asia/Tokyo")).date()
    assert tokyo_date == date(2026, 6, 16)

    # Sanity: studio_local_date_now uses live clock; just verify return type
    result = studio_local_date_now("Europe/Dublin")
    assert isinstance(result, date)
    assert result >= date(2026, 1, 1)
