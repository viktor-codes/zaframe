"""
ScheduleTemplate template and bulk occurrence generation schemas.
"""

from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScheduleTemplateBase(BaseModel):
    """Base fields for a recurring schedule template."""

    day_of_week: int = Field(..., ge=0, le=6, description="Day of week 0-6 (Mon-Sun)")
    start_time: time = Field(..., description="Wall-clock start time")
    valid_from: date = Field(..., description="Template valid from date")
    valid_to: date | None = Field(
        None,
        description="Template valid through date (inclusive)",
    )


class ScheduleTemplateCreate(ScheduleTemplateBase):
    """Create a schedule template for a service."""

    service_id: int = Field(..., description="Service ID")


class ScheduleTemplateResponse(ScheduleTemplateBase):
    """ScheduleTemplate template API response."""

    id: int
    service_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleGenerateRequest(BaseModel):
    """Request body for POST /studios/{id}/generate-occurrences (legacy route name TBD)."""

    service_id: int = Field(
        ...,
        description="ID of the service to generate course occurrences for",
        examples=[42],
    )
    days: list[int] = Field(
        ...,
        min_length=1,
        description="Days of week (0=Monday .. 6=Sunday); non-empty, no duplicates",
        examples=[[1, 3]],
    )
    start_time: time = Field(
        ...,
        description="Local start time for each occurrence (HH:MM or HH:MM:SS)",
        examples=["18:00:00", "18:00"],
    )
    weeks_count: int = Field(
        ...,
        ge=1,
        le=52,
        description="Number of weeks to generate occurrences for",
        examples=[6],
    )

    @field_validator("days")
    @classmethod
    def validate_days(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("days must not contain duplicates")
        for day in value:
            if not 0 <= day <= 6:
                raise ValueError("each day must be between 0 and 6")
        return value
