"""Pure capacity / overbooking helpers shared across catalog services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.modules.catalog.public.dto import PublicServiceAvailabilityDTO


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


def classify_occurrence_capacity(
    service: CapacityServiceLike,
    *,
    max_capacity: int,
    current_bookings: int,
    requested: int = 1,
) -> OccurrenceCapacityFlags:
    """Wrap Service.get_capacity_status and derive per-occurrence flags."""
    status = service.get_capacity_status(
        max_capacity=max_capacity,
        current_bookings=current_bookings,
        requested=requested,
    )
    is_over_hard = status == "HARD_LIMIT_REACHED"
    is_over_soft = status == "SOFT_LIMIT_REACHED"
    return OccurrenceCapacityFlags(
        is_over_soft=is_over_soft,
        is_over_hard=is_over_hard,
        remaining=max(0, max_capacity - current_bookings),
        total_after_one_booking=current_bookings + requested,
    )


def is_occurrence_overbooked(flags: OccurrenceCapacityFlags) -> bool:
    return flags.is_over_soft or flags.is_over_hard


def overbooking_status_label(flags: OccurrenceCapacityFlags) -> str | None:
    if flags.is_over_hard:
        return "HARD_LIMIT_REACHED"
    if flags.is_over_soft:
        return "SOFT_LIMIT_REACHED"
    return None


def evaluate_course_capacity_summary(
    service: CapacityServiceLike,
    fills: list[OccurrenceFill],
    *,
    requested_per_occurrence: int = 1,
) -> CourseCapacitySummary:
    """
    Shared ratio logic:
    - hard_block if any HARD_LIMIT or overbooked_ratio > max_overbooked_ratio
    - requires_warning if any soft/hard but not hard_block
    - can_book if not hard_block (callers may refine with remaining seats)
    """
    if not fills:
        return CourseCapacitySummary(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_count=0,
            total_occurrences=0,
        )

    overbooked_count = 0
    any_hard = False

    for fill in fills:
        flags = classify_occurrence_capacity(
            service,
            max_capacity=fill.max_capacity,
            current_bookings=fill.current_total,
            requested=requested_per_occurrence,
        )
        if is_occurrence_overbooked(flags):
            overbooked_count += 1
        if flags.is_over_hard:
            any_hard = True

    overbooked_ratio = overbooked_count / len(fills)
    hard_block = any_hard or overbooked_ratio > service.max_overbooked_ratio
    requires_warning = overbooked_count > 0 and not hard_block

    return CourseCapacitySummary(
        can_book=not hard_block,
        requires_warning=requires_warning,
        hard_block=hard_block,
        overbooked_count=overbooked_count,
        total_occurrences=len(fills),
    )


def build_public_course_availability(
    service: CapacityServiceLike,
    fills: list[OccurrenceFill],
    *,
    occurrence_dates: list[date],
) -> PublicServiceAvailabilityDTO:
    """Map capacity summary to storefront course card availability."""
    from app.modules.catalog.public.dto import PublicServiceAvailabilityDTO

    if len(occurrence_dates) != len(fills):
        msg = "occurrence_dates must be parallel to fills"
        raise ValueError(msg)

    total_remaining_capacity = 0
    overbooked_dates: list[date] = []

    for fill, occ_date in zip(fills, occurrence_dates, strict=True):
        flags = classify_occurrence_capacity(
            service,
            max_capacity=fill.max_capacity,
            current_bookings=fill.current_total,
        )
        total_remaining_capacity += flags.remaining
        if is_occurrence_overbooked(flags):
            overbooked_dates.append(occ_date)

    summary = evaluate_course_capacity_summary(service, fills)

    can_book = (
        len(fills) > 0 and total_remaining_capacity > 0 and not summary.hard_block
    )

    return PublicServiceAvailabilityDTO(
        can_book=can_book,
        total_remaining_capacity=total_remaining_capacity,
        requires_warning=summary.requires_warning,
        overbooked_dates=sorted(set(overbooked_dates)),
    )
