from __future__ import annotations

"""
Pydantic schemas for studio and service search.

WHY: search is a read-only leaf — it must not import catalog modules.
Response shapes mirror catalog public schemas for API compatibility.
"""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field

from app.models import ServiceCategory, ServiceType, ServiceVisibility

ServiceVisibilityLiteral = Literal["draft", "published", "archived"]


class SearchStudioResponse(BaseModel):
    """Studio fields returned in search results."""

    id: int
    owner_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    amenities: list[str] = Field(default_factory=list)
    timezone: str
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class SearchServiceResponse(BaseModel):
    """Service fields returned in search results."""

    id: int
    studio_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    type: str = Field(default=ServiceType.SINGLE)
    category: ServiceCategory = Field(default=ServiceCategory.YOGA)
    duration_minutes: int = Field(..., ge=1)
    max_capacity: int = Field(..., ge=1)
    price_single_cents: int = Field(..., ge=0)
    price_course_cents: int | None = Field(None, ge=0)
    soft_limit_ratio: float = Field(1.0, ge=1.0, le=2.0)
    hard_limit_ratio: float = Field(1.5, ge=1.0, le=3.0)
    max_overbooked_ratio: float = Field(0.3, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    visibility: ServiceVisibilityLiteral = Field(default=ServiceVisibility.PUBLISHED)
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class SearchQueryParams(BaseModel):
    """
    Search parameters for the public API.

    All fields are optional and can be combined.
    """

    query: str | None = Field(
        None,
        description="Search query for name/description",
    )
    category: ServiceCategory | None = Field(
        None,
        description="Service category filter",
    )
    city: str | None = Field(
        None,
        description="City filter for studios",
    )
    lat: float | None = Field(
        None,
        description="Latitude for geo search",
    )
    lng: float | None = Field(
        None,
        description="Longitude for geo search",
    )
    radius_km: int | None = Field(
        10,
        ge=0,
        description="Search radius in kilometres (default 10 km)",
    )
    amenities: list[str] | None = Field(
        None,
        description="Required studio amenities",
    )


class SearchResult(BaseModel):
    """Search hit: studio plus matching services."""

    studio: SearchStudioResponse
    matched_services: list[SearchServiceResponse]
