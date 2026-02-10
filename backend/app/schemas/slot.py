"""
Pydantic schemas для Slot модели.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SlotBase(BaseModel):
    """Базовые поля слота."""
    start_time: datetime = Field(..., description="Время начала занятия")
    end_time: datetime = Field(..., description="Время окончания занятия")
    title: str = Field(..., min_length=1, max_length=200, description="Название класса")
    description: str | None = Field(None, max_length=1000, description="Описание класса")
    max_capacity: int = Field(default=10, ge=1, description="Максимальное количество мест")
    price_cents: int = Field(default=0, ge=0, description="Цена за место в центах")
    course_price_cents: int | None = Field(
        None,
        ge=0,
        description="Цена за посещение в рамках курса (если отличается от обычной)",
    )


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
    is_active: bool | None = None


class SlotResponse(SlotBase):
    """Схема для ответа API."""
    id: int
    studio_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SlotWithBookings(SlotResponse):
    """Слот с информацией о бронированиях."""
    bookings_count: int = Field(default=0, description="Количество бронирований")
    available_spots: int = Field(..., description="Доступные места")

    class Config:
        from_attributes = True
