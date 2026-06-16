"""
Public storefront schemas (anonymous / catalog perspective).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PublicOccurrence(BaseModel):
    """Occurrence summary for public studio catalog."""

    id: int
    start_time: datetime
    is_full: bool


class PublicService(BaseModel):
    """Public service card for the storefront (polaroid listing)."""

    id: int
    name: str
    description: str | None
    type: str
    duration_minutes: int
    max_capacity: int
    price_single_cents: int
    price_course_cents: int | None
    cover_image_url: str | None = Field(
        None,
        description="Cover image URL (optional, configured later)",
    )
    next_term_start: datetime | None = Field(
        None,
        description="Start of the nearest occurrence in the current term",
    )
    term_end: datetime | None = Field(
        None,
        description="End of the last occurrence in the current term",
    )
    occurrences_count: int = Field(
        0,
        description="Number of occurrences in the current (nearest) term",
    )

    class Availability(BaseModel):
        """Aggregated course availability for the card."""

        can_book: bool
        total_remaining_capacity: int
        requires_warning: bool
        overbooked_dates: list[date] = Field(
            default_factory=list,
            description="Dates where booking would cause overbooking",
        )

    availability: Availability | None = Field(
        None,
        description="Course booking availability summary",
    )


class StudioPublicResponse(BaseModel):
    """Public studio page: profile + service catalog."""

    id: int
    name: str
    slug: str | None
    description: str | None
    services: list[PublicService] = Field(default_factory=list)
