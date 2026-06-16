"""Domain DTOs for service availability flows (no Pydantic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class CourseBookingPreviewItemDTO:
    occurrence_id: int
    start_time: datetime
    max_capacity: int
    confirmed_count: int
    pending_count: int
    total_after_booking: int
    is_over_soft_limit: bool
    is_over_hard_limit: bool


@dataclass(frozen=True, slots=True)
class CourseAvailabilityDTO:
    can_book: bool
    requires_warning: bool
    hard_block: bool
    overbooked_occurrences: list[CourseBookingPreviewItemDTO] = field(
        default_factory=lambda: list[CourseBookingPreviewItemDTO]()
    )
    message: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceAvailabilityScheduleItemDTO:
    date: date
    is_overbooked: bool
    remaining: int
    overbooking_status: str | None


@dataclass(frozen=True, slots=True)
class ServiceAvailabilityDTO:
    service_id: int
    can_book: bool
    requires_warning: bool
    warning_message: str | None
    schedule_details: list[ServiceAvailabilityScheduleItemDTO] = field(
        default_factory=lambda: list[ServiceAvailabilityScheduleItemDTO]()
    )
