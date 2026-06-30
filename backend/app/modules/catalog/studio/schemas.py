"""
Pydantic schemas for the Studio model.
"""

import re

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.datetime_utils import validate_iana_timezone
from app.core.exceptions import ValidationError as AppValidationError

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_studio_slug(value: str | None) -> str | None:
    """Normalize and validate a URL-safe studio slug."""
    if value is None:
        return None
    normalized = value.strip().lower()
    if not SLUG_PATTERN.fullmatch(normalized):
        raise ValueError("Slug must use lowercase letters, numbers, and single hyphens")
    return normalized


class StudioBase(BaseModel):
    """Base studio fields."""

    name: str = Field(..., min_length=1, max_length=200, description="Studio name")
    slug: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="URL-safe public studio slug",
        examples=["yoga-hub-dublin"],
    )
    description: str | None = Field(None, description="Studio description")
    logo_url: str | None = Field(
        None,
        max_length=2048,
        description="Public logo image URL",
        examples=["https://cdn.example.com/studios/yoga-hub/logo.png"],
    )
    cover_url: str | None = Field(
        None,
        max_length=2048,
        description="Public cover image URL",
        examples=["https://cdn.example.com/studios/yoga-hub/cover.jpg"],
    )
    email: EmailStr | None = Field(None, description="Studio email")
    phone: str | None = Field(None, max_length=20, description="Studio phone")
    address: str | None = Field(None, max_length=500, description="Studio address")
    city: str | None = Field(None, max_length=100, description="Studio city")
    latitude: float | None = Field(None, description="Studio latitude")
    longitude: float | None = Field(None, description="Studio longitude")
    amenities: list[str] = Field(
        default_factory=list,
        description="Studio amenities/options, e.g. shower or parking",
    )
    cancel_before_hours: int = Field(
        24,
        ge=0,
        le=720,
        description="Customer cancellation cutoff before occurrence start, in hours",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        return validate_studio_slug(value)


class StudioCreate(StudioBase):
    """Schema for creating a studio; owner_id is set from the router-level token."""

    owner_id: int | None = Field(None, description="Owner ID set from the token")
    timezone: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="IANA timezone of the studio (required at onboarding, e.g. Europe/Berlin)",
        examples=["Europe/Berlin", "America/New_York", "Asia/Tokyo"],
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            return validate_iana_timezone(value)
        except AppValidationError as exc:
            raise ValueError(exc.detail) from exc


class StudioUpdate(BaseModel):
    """Schema for updating a studio; all fields are optional."""

    name: str | None = Field(None, min_length=1, max_length=200)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    logo_url: str | None = Field(None, max_length=2048)
    cover_url: str | None = Field(None, max_length=2048)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    amenities: list[str] | None = None
    is_active: bool | None = None
    cancel_before_hours: int | None = Field(
        None,
        ge=0,
        le=720,
        description="Customer cancellation cutoff before occurrence start, in hours",
    )
    timezone: str | None = Field(
        None,
        min_length=1,
        max_length=64,
        description="IANA timezone (immutable after first occurrence is created)",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        return validate_studio_slug(value)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_iana_timezone(value)
        except AppValidationError as exc:
            raise ValueError(exc.detail) from exc


class StudioResponse(StudioBase):
    """API response schema."""

    id: int
    owner_id: int
    timezone: str
    is_active: bool
    cancel_before_hours: int
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class StudioRoleResponse(BaseModel):
    """Current user's role in one studio."""

    studio_id: int = Field(..., description="Studio ID")
    role: str = Field(..., description="Studio membership role")


class StudioWithRoleResponse(StudioResponse):
    """Studio response enriched with the current user's membership role."""

    role: str = Field(..., description="Current user's role in this studio")


class StudioWithOccurrences(StudioResponse):
    """Studio with occurrence count (for list views)."""

    occurrences_count: int | None = Field(None, description="Number of occurrences")

    model_config = ConfigDict(from_attributes=True)
