from datetime import date

from app.models.service import Service
from app.modules.catalog.capacity import (
    OccurrenceFill,
    build_public_course_availability,
    classify_occurrence_capacity,
    evaluate_course_capacity_summary,
)


class DummyService:
    """Minimal service double for capacity helpers."""

    def __init__(
        self,
        *,
        soft_limit_ratio: float,
        hard_limit_ratio: float,
        max_overbooked_ratio: float = 0.3,
    ) -> None:
        self.soft_limit_ratio = soft_limit_ratio
        self.hard_limit_ratio = hard_limit_ratio
        self.max_overbooked_ratio = max_overbooked_ratio

    def get_capacity_status(
        self,
        *,
        max_capacity: int,
        current_bookings: int,
        requested: int = 1,
    ) -> str | None:
        return Service.get_capacity_status(
            self,
            max_capacity=max_capacity,
            current_bookings=current_bookings,
            requested=requested,
        )


def test_classify_occurrence_capacity_under_soft_limit() -> None:
    service = DummyService(soft_limit_ratio=1.0, hard_limit_ratio=1.5)

    flags = classify_occurrence_capacity(
        service,
        max_capacity=10,
        current_bookings=8,
    )

    assert flags.is_over_soft is False
    assert flags.is_over_hard is False
    assert flags.remaining == 2
    assert flags.total_after_one_booking == 9


def test_classify_occurrence_capacity_soft_limit() -> None:
    service = DummyService(soft_limit_ratio=1.0, hard_limit_ratio=1.5)

    flags = classify_occurrence_capacity(
        service,
        max_capacity=10,
        current_bookings=10,
    )

    assert flags.is_over_soft is True
    assert flags.is_over_hard is False


def test_evaluate_course_capacity_summary_hard_block_on_ratio() -> None:
    service = DummyService(
        soft_limit_ratio=1.0,
        hard_limit_ratio=2.0,
        max_overbooked_ratio=0.3,
    )
    fills = [
        OccurrenceFill(1, 10, 10, 0),
        OccurrenceFill(2, 10, 10, 0),
        OccurrenceFill(3, 10, 0, 0),
        OccurrenceFill(4, 10, 0, 0),
        OccurrenceFill(5, 10, 0, 0),
    ]

    summary = evaluate_course_capacity_summary(service, fills)

    assert summary.hard_block is True
    assert summary.can_book is False
    assert summary.overbooked_count == 2
    assert summary.total_occurrences == 5


def test_evaluate_course_capacity_summary_warning_only() -> None:
    service = DummyService(
        soft_limit_ratio=1.0,
        hard_limit_ratio=2.0,
        max_overbooked_ratio=0.5,
    )
    fills = [
        OccurrenceFill(1, 10, 10, 0),
        OccurrenceFill(2, 10, 0, 0),
        OccurrenceFill(3, 10, 0, 0),
    ]

    summary = evaluate_course_capacity_summary(service, fills)

    assert summary.hard_block is False
    assert summary.requires_warning is True
    assert summary.can_book is True
    assert summary.overbooked_count == 1


def test_build_public_course_availability_maps_dates() -> None:
    service = DummyService(
        soft_limit_ratio=1.0,
        hard_limit_ratio=2.0,
        max_overbooked_ratio=0.5,
    )
    fills = [
        OccurrenceFill(1, 10, 10, 0),
        OccurrenceFill(2, 10, 0, 0),
    ]
    occurrence_dates = [date(2026, 6, 1), date(2026, 6, 8)]

    availability = build_public_course_availability(
        service,
        fills,
        occurrence_dates=occurrence_dates,
    )

    assert availability.overbooked_dates == [date(2026, 6, 1)]
    assert availability.requires_warning is True
    assert availability.can_book is True
    assert availability.total_remaining_capacity == 10
