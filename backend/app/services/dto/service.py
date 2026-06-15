"""Domain DTOs for service/booking public flows (no Pydantic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.models import Booking, Order


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
    overbooked_occurrences: list[CourseBookingPreviewItemDTO] = field(default_factory=list)
    message: str | None = None


@dataclass(frozen=True, slots=True)
class CourseBookingInput:
    service_id: int
    guest_name: str
    guest_email: str
    guest_phone: str | None


@dataclass(frozen=True, slots=True)
class CourseBookingResultDTO:
    order: Order
    bookings: list[Booking]
    availability: CourseAvailabilityDTO


@dataclass(frozen=True, slots=True)
class PublicServiceAvailabilityDTO:
    can_book: bool
    total_remaining_capacity: int
    requires_warning: bool
    overbooked_dates: list[date] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PublicServiceDTO:
    id: int
    name: str
    description: str | None
    type: str
    duration_minutes: int
    max_capacity: int
    price_single_cents: int
    price_course_cents: int | None
    cover_image_url: str | None
    next_term_start: datetime | None
    term_end: datetime | None
    occurrences_count: int
    availability: PublicServiceAvailabilityDTO | None = None


@dataclass(frozen=True, slots=True)
class StudioPublicDTO:
    id: int
    name: str
    slug: str | None
    description: str | None
    services: list[PublicServiceDTO] = field(default_factory=list)


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
    schedule_details: list[ServiceAvailabilityScheduleItemDTO] = field(default_factory=list)
