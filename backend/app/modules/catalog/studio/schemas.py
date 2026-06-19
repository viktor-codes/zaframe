"""
Pydantic schemas для Studio модели.
"""

import re

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.datetime_utils import validate_iana_timezone

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
    """Базовые поля студии."""

    name: str = Field(..., min_length=1, max_length=200, description="Название студии")
    slug: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="URL-safe public studio slug",
        examples=["yoga-hub-dublin"],
    )
    description: str | None = Field(None, description="Описание студии")
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
    email: EmailStr | None = Field(None, description="Email студии")
    phone: str | None = Field(None, max_length=20, description="Телефон студии")
    address: str | None = Field(None, max_length=500, description="Адрес студии")
    city: str | None = Field(None, max_length=100, description="Город студии")
    latitude: float | None = Field(None, description="Широта студии")
    longitude: float | None = Field(None, description="Долгота студии")
    amenities: list[str] = Field(
        default_factory=list,
        description="Список удобств/опций студии (например, душ, парковка)",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        return validate_studio_slug(value)


class StudioCreate(StudioBase):
    """Схема для создания студии. owner_id передаётся из токена на уровне роутера."""

    owner_id: int | None = Field(None, description="ID владельца (устанавливается из токена)")
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
        return validate_iana_timezone(value)


class StudioUpdate(BaseModel):
    """Схема для обновления студии (все поля опциональные)."""

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
        return validate_iana_timezone(value)


class StudioResponse(StudioBase):
    """Схема для ответа API."""

    id: int
    owner_id: int
    timezone: str
    is_active: bool
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
