"""
Pydantic schemas for bulk schedule (slot) generation.
"""

from __future__ import annotations

from datetime import time

from pydantic import BaseModel, Field, field_validator


class ScheduleGenerateRequest(BaseModel):
    """Request body for POST /studios/{id}/generate-schedule."""

    service_id: int = Field(
        ...,
        description="ID of the service to generate course sessions for",
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
        description="Local start time for each session (HH:MM or HH:MM:SS)",
        examples=["18:00:00", "18:00"],
    )
    weeks_count: int = Field(
        ...,
        ge=1,
        le=52,
        description="Number of weeks to generate sessions for",
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
