"""
Pydantic schemas for Occurrence model (concrete bookable session in time).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import AliasPath, AwareDatetime, BaseModel, ConfigDict, Field, field_validator

OccurrenceStatusLiteral = Literal["scheduled", "cancelled", "completed"]


def _normalize_to_utc(value: datetime) -> datetime:
    """Normalize timezone-aware instants to UTC for a stable API contract."""
    return value.astimezone(UTC)


class OccurrenceBase(BaseModel):
    """Base fields for an occurrence."""

    start_time: AwareDatetime = Field(
        ...,
        description="Occurrence start instant (timezone-aware ISO 8601)",
    )
    end_time: AwareDatetime = Field(
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
    def normalize_instant_to_utc(cls, value: datetime) -> datetime:
        return _normalize_to_utc(value)


class OccurrenceCreate(OccurrenceBase):
    """Create an occurrence."""

    studio_id: int = Field(..., description="Studio ID")
    service_id: int = Field(
        ...,
        description="Service ID for the bookable class/course occurrence",
    )
    instructor_id: int | None = Field(
        None,
        description="Studio member ID assigned to teach this occurrence",
    )


class OccurrenceUpdate(BaseModel):
    """Partial occurrence update."""

    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    max_capacity: int | None = Field(None, ge=1)
    price_cents: int | None = Field(None, ge=0)
    instructor_id: int | None = Field(
        None,
        description="Studio member ID assigned to teach this occurrence",
    )
    status: OccurrenceStatusLiteral | None = Field(None, description="Occurrence status")
    cancellation_reason: str | None = Field(
        None,
        max_length=500,
        description="Reason shown when status is cancelled",
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_instant_to_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _normalize_to_utc(value)


class OccurrenceInstructorResponse(BaseModel):
    """Instructor display data embedded in occurrence responses."""

    studio_member_id: int = Field(
        ...,
        validation_alias="id",
        description="Studio member ID assigned as instructor",
    )
    user_id: int = Field(..., description="Instructor user ID")
    name: str = Field(
        ...,
        validation_alias=AliasPath("user", "name"),
        description="Instructor display name",
    )
    role: str = Field(..., description="Studio member role")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OccurrenceResponse(OccurrenceBase):
    """Occurrence API response."""

    id: int
    studio_id: int
    service_id: int
    instructor_id: int | None = Field(None, description="Assigned studio member ID")
    instructor: OccurrenceInstructorResponse | None = Field(
        None,
        description="Assigned instructor display data",
    )
    status: OccurrenceStatusLiteral
    cancelled_at: AwareDatetime | None = Field(
        None,
        description="UTC timestamp when the occurrence was cancelled",
    )
    cancellation_reason: str | None = Field(
        None,
        description="Owner-provided cancellation reason",
    )
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class OccurrenceWithBookings(OccurrenceResponse):
    """Occurrence with booking occupancy summary."""

    bookings_count: int = Field(default=0, description="Number of bookings")
    available_spots: int = Field(..., description="Remaining seats")

    model_config = ConfigDict(from_attributes=True)
