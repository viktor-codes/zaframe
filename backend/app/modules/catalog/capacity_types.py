"""Capacity / overbooking types shared across catalog services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class CapacityServiceLike(Protocol):
    """Minimal service surface for capacity math (ORM model or test doubles)."""

    soft_limit_ratio: float
    hard_limit_ratio: float
    max_overbooked_ratio: float

    def get_capacity_status(
        self,
        *,
        max_capacity: int,
        current_bookings: int,
        requested: int = 1,
    ) -> str | None: ...


@dataclass(frozen=True, slots=True)
class OccurrenceFill:
    occurrence_id: int
    max_capacity: int
    confirmed_count: int
    pending_count: int

    @property
    def current_total(self) -> int:
        return self.confirmed_count + self.pending_count


@dataclass(frozen=True, slots=True)
class OccurrenceCapacityFlags:
    is_over_soft: bool
    is_over_hard: bool
    remaining: int
    total_after_one_booking: int


@dataclass(frozen=True, slots=True)
class CourseCapacitySummary:
    can_book: bool
    requires_warning: bool
    hard_block: bool
    overbooked_count: int
    total_occurrences: int
