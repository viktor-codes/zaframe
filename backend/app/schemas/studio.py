"""
Pydantic schemas для Studio модели.
"""

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.datetime_utils import validate_iana_timezone


class StudioBase(BaseModel):
    """Базовые поля студии."""

    name: str = Field(..., min_length=1, max_length=200, description="Название студии")
    description: str | None = Field(None, description="Описание студии")
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
    description: str | None = None
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


class StudioWithOccurrences(StudioResponse):
    """Studio with occurrence count (for list views)."""

    occurrences_count: int | None = Field(None, description="Number of occurrences")

    model_config = ConfigDict(from_attributes=True)
