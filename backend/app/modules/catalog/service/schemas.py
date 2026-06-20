"""
Pydantic schemas for Service (sellable offering container).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import ServiceCategory, ServiceType, ServiceVisibility

ServiceVisibilityLiteral = Literal["draft", "published", "archived"]


class ServiceBase(BaseModel):
    """Base service fields."""

    name: str = Field(..., min_length=1, max_length=200, description="Service name")
    description: str | None = Field(
        None,
        max_length=1000,
        description="Service description",
    )
    type: str = Field(
        default=ServiceType.SINGLE,
        description="Offering type: single or course (DB migration to 'single' pending)",
    )
    category: ServiceCategory = Field(
        default=ServiceCategory.YOGA,
        description="Service category (yoga, boxing, dance, etc.)",
    )
    duration_minutes: int = Field(..., ge=1, description="Session duration in minutes")
    max_capacity: int = Field(..., ge=1, description="Maximum capacity")
    price_single_cents: int = Field(
        ...,
        ge=0,
        description="Drop-in price per occurrence in cents",
    )
    price_course_cents: int | None = Field(
        None,
        ge=0,
        description="Full course price in cents when type=course",
    )
    soft_limit_ratio: float = Field(
        1.0,
        ge=1.0,
        le=2.0,
        description="Soft limit ratio relative to max_capacity",
    )
    hard_limit_ratio: float = Field(
        1.5,
        ge=1.0,
        le=3.0,
        description="Hard limit ratio relative to max_capacity",
    )
    max_overbooked_ratio: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Share of occurrences allowed to enter overbooking",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Service tags (e.g. beginner, evening, women_only)",
    )
    visibility: ServiceVisibilityLiteral = Field(
        default=ServiceVisibility.PUBLISHED,
        description="Product lifecycle state: draft, published, or archived",
        examples=[ServiceVisibility.PUBLISHED],
    )


class ServiceCreate(ServiceBase):
    """Create a service."""

    studio_id: int = Field(..., description="Studio ID")


class ServiceUpdate(BaseModel):
    """Partial service update."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    type: str | None = Field(None, description="Offering type")
    category: ServiceCategory | None = Field(
        None,
        description="Service category",
    )
    duration_minutes: int | None = Field(None, ge=1)
    max_capacity: int | None = Field(None, ge=1)
    price_single_cents: int | None = Field(None, ge=0)
    price_course_cents: int | None = Field(None, ge=0)
    is_active: bool | None = None
    visibility: ServiceVisibilityLiteral | None = Field(
        None,
        description="Product lifecycle state: draft, published, or archived",
        examples=[ServiceVisibility.ARCHIVED],
    )
    soft_limit_ratio: float | None = Field(
        None,
        ge=1.0,
        le=2.0,
        description="Soft limit ratio relative to max_capacity",
    )
    hard_limit_ratio: float | None = Field(
        None,
        ge=1.0,
        le=3.0,
        description="Hard limit ratio relative to max_capacity",
    )
    max_overbooked_ratio: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Share of occurrences allowed to enter overbooking",
    )
    tags: list[str] | None = Field(
        None,
        description="Service tags",
    )


class ServiceResponse(ServiceBase):
    """Service API response."""

    id: int
    studio_id: int
    is_active: bool
    visibility: ServiceVisibilityLiteral
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServiceAvailabilityScheduleItem(BaseModel):
    """Single course date row for availability pre-check."""

    date: date
    is_overbooked: bool
    remaining: int
    overbooking_status: str | None = Field(
        None,
        description="SOFT_LIMIT_REACHED / HARD_LIMIT_REACHED or None",
    )


class ServiceAvailabilityResponse(BaseModel):
    """Detailed course availability for the purchase modal."""

    service_id: int
    can_book: bool
    requires_warning: bool
    warning_message: str | None
    schedule_details: list[ServiceAvailabilityScheduleItem]
