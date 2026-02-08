"""
Pydantic schemas для Booking модели.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.booking import BookingStatus


class BookingBase(BaseModel):
    """Базовые поля бронирования."""
    slot_id: int = Field(..., description="ID слота для бронирования")


class BookingCreate(BookingBase):
    """
    Схема для создания бронирования (гостевой режим).
    
    Используется для гостевых бронирований до активации аккаунта.
    После Magic Link данные переносятся в User.
    """
    guest_name: str = Field(..., min_length=1, max_length=100, description="Имя гостя")
    guest_email: EmailStr = Field(..., description="Email гостя")
    guest_phone: str | None = Field(None, max_length=20, description="Телефон гостя (опционально)")


class BookingCreateAuthenticated(BookingBase):
    """
    Схема для создания бронирования зарегистрированным пользователем.
    
    user_id берётся из токена аутентификации.
    """
    pass


class BookingUpdate(BaseModel):
    """Схема для обновления бронирования."""
    status: str | None = Field(None, description="Статус бронирования")
    payment_intent_id: str | None = Field(None, description="ID платежа Stripe")
    payment_status: str | None = Field(None, description="Статус платежа")


class BookingResponse(BookingBase):
    """Схема для ответа API."""
    id: int
    user_id: int | None
    guest_session_id: str | None
    guest_name: str | None
    guest_email: str | None
    guest_phone: str | None
    status: str
    checkout_session_id: str | None
    payment_intent_id: str | None
    payment_status: str | None
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None

    class Config:
        from_attributes = True


class BookingWithSlot(BookingResponse):
    """Бронирование с информацией о слоте."""
    slot: "SlotResponse" = Field(..., description="Информация о слоте")

    class Config:
        from_attributes = True


class BookingWithUser(BookingResponse):
    """Бронирование с информацией о пользователе."""
    user: "UserPublic | None" = Field(None, description="Информация о пользователе")

    class Config:
        from_attributes = True


class BookingCancel(BaseModel):
    """Схема для отмены бронирования."""
    reason: str | None = Field(None, max_length=500, description="Причина отмены")
