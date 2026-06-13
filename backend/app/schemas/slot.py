"""
Pydantic schemas для Slot модели.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SlotStatusLiteral = Literal["active", "cancelled"]


def _require_timezone_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Datetime must include timezone (ISO 8601 with Z or offset)")
    return value.astimezone(UTC)


class SlotBase(BaseModel):
    """Базовые поля слота."""

    start_time: datetime = Field(..., description="Slot start instant (timezone-aware ISO 8601)")
    end_time: datetime = Field(..., description="Slot end instant (timezone-aware ISO 8601)")
    title: str = Field(..., min_length=1, max_length=200, description="Название класса")
    description: str | None = Field(None, max_length=1000, description="Описание класса")
    max_capacity: int = Field(default=10, ge=1, description="Максимальное количество мест")
    price_cents: int = Field(default=0, ge=0, description="Цена за место в центах")
    course_price_cents: int | None = Field(
        None,
        ge=0,
        description="Цена за посещение в рамках курса (если отличается от обычной)",
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_instant(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value)


class SlotCreate(SlotBase):
    """Схема для создания слота."""

    studio_id: int = Field(..., description="ID студии")
    service_id: int | None = Field(
        None,
        description="ID услуги (Service), если слот привязан к услуге/курсу",
    )


class SlotUpdate(BaseModel):
    """Схема для обновления слота (все поля опциональные)."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    max_capacity: int | None = Field(None, ge=1)
    price_cents: int | None = Field(None, ge=0)
    status: SlotStatusLiteral | None = Field(None, description="Статус занятия")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_instant(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _require_timezone_aware(value)


class SlotResponse(SlotBase):
    """Схема для ответа API."""

    id: int
    studio_id: int
    status: SlotStatusLiteral
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SlotWithBookings(SlotResponse):
    """Слот с информацией о бронированиях."""

    bookings_count: int = Field(default=0, description="Количество бронирований")
    available_spots: int = Field(..., description="Доступные места")

    model_config = ConfigDict(from_attributes=True)
