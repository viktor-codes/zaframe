"""
Pydantic schemas для Booking модели.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.models.booking import BookingType
from app.schemas.slot import SlotResponse
from app.schemas.studio import StudioResponse
from app.schemas.user import UserPublic


class BookingBase(BaseModel):
    """Базовые поля бронирования."""

    slot_id: int = Field(..., description="ID слота для бронирования")


class BookingCreate(BookingBase):
    """
    Схема для создания бронирования (гостевой режим).

    Используется для гостевых бронирований до OTP-верификации.
    После verify user_id проставляется на booking.
    """

    guest_name: str = Field(..., min_length=1, max_length=100, description="Имя гостя")
    guest_email: EmailStr = Field(..., description="Email гостя")
    guest_phone: str | None = Field(None, max_length=20, description="Телефон гостя (опционально)")
    booking_type: str = Field(
        default=BookingType.SINGLE,
        description="Тип бронирования: single или course",
    )
    service_id: int | None = Field(
        None,
        description="ID услуги (обязательно для курса)",
    )


class BookingCreateAuthenticated(BookingBase):
    """
    Схема для создания бронирования зарегистрированным пользователем.

    user_id берётся из токена аутентификации.
    """

    pass


class BookingClientBase(BookingBase):
    """
    Общие поля клиентских ответов по бронированию.

    Stripe checkout_session_id и payment_intent_id намеренно исключены.
    """

    id: int
    user_id: int | None
    status: str
    reserved_until: datetime | None = Field(
        None,
        description="UTC timestamp until which a pending booking reserves slot capacity",
    )
    payment_status: str | None = Field(
        None,
        description="Статус платежа (без внутренних Stripe ID)",
    )
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_guest_booking(self) -> bool:
        """True when booking was created without a linked user account."""
        return self.user_id is None


class BookingSelfResponse(BookingClientBase):
    """
    Ответ для владельца брони (гость или авторизованный пользователь).

    Содержит собственные контактные данные; без внутренних платёжных ID.
    """

    guest_name: str | None = Field(None, description="Имя на бронировании")
    guest_email: str | None = Field(None, description="Email на бронировании")
    guest_phone: str | None = Field(None, description="Телефон на бронировании")


class BookingOwnerResponse(BookingClientBase):
    """
    Ответ для владельца студии.

    Контакты гостя для связи; payment_status без checkout_session_id / payment_intent_id.
    """

    guest_name: str | None = Field(None, description="Имя гостя")
    guest_email: str | None = Field(None, description="Email гостя для связи")
    guest_phone: str | None = Field(None, description="Телефон гостя для связи")


class BookingWithSlot(BookingOwnerResponse):
    """Бронирование с информацией о слоте (кабинет владельца студии)."""

    slot: SlotResponse = Field(..., description="Информация о слоте")

    model_config = ConfigDict(from_attributes=True)


class BookingWithUser(BookingOwnerResponse):
    """Бронирование с информацией о пользователе (кабинет владельца студии)."""

    user: UserPublic | None = Field(None, description="Информация о пользователе")

    model_config = ConfigDict(from_attributes=True)


class BookingListItem(BookingSelfResponse):
    """
    Элемент списка бронирований для личного кабинета (/bookings/my).

    Вложенные slot+studio, чтобы фронт не делал N+1.
    """

    slot: SlotResponse = Field(..., description="Информация о слоте")
    studio: StudioResponse = Field(..., description="Информация о студии")

    model_config = ConfigDict(from_attributes=True)


class BookingCancel(BaseModel):
    """Схема для отмены бронирования."""

    reason: str | None = Field(None, max_length=500, description="Причина отмены")
