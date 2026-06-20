"""Domain DTOs for the anonymous storefront aggregate (no Pydantic)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class PublicServiceAvailabilityDTO:
    can_book: bool
    total_remaining_capacity: int
    requires_warning: bool
    overbooked_dates: list[date] = field(default_factory=lambda: list[date]())


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
    logo_url: str | None
    cover_url: str | None
    services: list[PublicServiceDTO] = field(default_factory=lambda: list[PublicServiceDTO]())
