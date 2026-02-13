"""
Pydantic schemas для Studio модели.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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


class StudioUpdate(BaseModel):
    """Схема для обновления студии (все поля опциональные)."""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class StudioResponse(StudioBase):
    """Схема для ответа API."""
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudioWithSlots(StudioResponse):
    """Студия с количеством слотов (для списков)."""
    slots_count: int | None = Field(None, description="Количество слотов")

    class Config:
        from_attributes = True
