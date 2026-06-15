"""
Pydantic schemas for Occurrence model (concrete bookable session in time).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

OccurrenceStatusLiteral = Literal["active", "cancelled"]


def _require_timezone_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Datetime must include timezone (ISO 8601 with Z or offset)")
    return value.astimezone(UTC)


class OccurrenceBase(BaseModel):
    """Base fields for an occurrence."""

    start_time: datetime = Field(
        ...,
        description="Occurrence start instant (timezone-aware ISO 8601)",
    )
    end_time: datetime = Field(
        ...,
        description="Occurrence end instant (timezone-aware ISO 8601)",
    )
    title: str = Field(..., min_length=1, max_length=200, description="Class title")
    description: str | None = Field(None, max_length=1000, description="Class description")
    max_capacity: int = Field(default=10, ge=1, description="Maximum capacity")
    price_cents: int = Field(default=0, ge=0, description="Drop-in price per seat in cents")
    course_price_cents: int | None = Field(
        None,
        ge=0,
        description="Course-attendee price for this occurrence when different from drop-in",
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_instant(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value)


class OccurrenceCreate(OccurrenceBase):
    """Create an occurrence."""

    studio_id: int = Field(..., description="Studio ID")
    service_id: int | None = Field(
        None,
        description="Service ID when occurrence belongs to a service/course",
    )


class OccurrenceUpdate(BaseModel):
    """Partial occurrence update."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    max_capacity: int | None = Field(None, ge=1)
    price_cents: int | None = Field(None, ge=0)
    status: OccurrenceStatusLiteral | None = Field(None, description="Occurrence status")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_instant(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _require_timezone_aware(value)


class OccurrenceResponse(OccurrenceBase):
    """Occurrence API response."""

    id: int
    studio_id: int
    status: OccurrenceStatusLiteral
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OccurrenceWithBookings(OccurrenceResponse):
    """Occurrence with booking occupancy summary."""

    bookings_count: int = Field(default=0, description="Number of bookings")
    available_spots: int = Field(..., description="Remaining seats")

    model_config = ConfigDict(from_attributes=True)
