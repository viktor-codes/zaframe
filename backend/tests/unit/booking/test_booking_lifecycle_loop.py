"""Unit tests for the booking lifecycle worker loop helpers."""

from scripts.run_booking_lifecycle_loop import DEFAULT_INTERVAL_SECONDS, _interval_seconds


def test_interval_seconds_defaults_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("BOOKING_LIFECYCLE_INTERVAL_SECONDS", raising=False)
    assert _interval_seconds() == DEFAULT_INTERVAL_SECONDS


def test_interval_seconds_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("BOOKING_LIFECYCLE_INTERVAL_SECONDS", "120")
    assert _interval_seconds() == 120


def test_interval_seconds_rejects_too_small_and_invalid(monkeypatch) -> None:
    monkeypatch.setenv("BOOKING_LIFECYCLE_INTERVAL_SECONDS", "5")
    assert _interval_seconds() == DEFAULT_INTERVAL_SECONDS
    monkeypatch.setenv("BOOKING_LIFECYCLE_INTERVAL_SECONDS", "nope")
    assert _interval_seconds() == DEFAULT_INTERVAL_SECONDS
