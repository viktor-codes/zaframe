"""
Модель Booking - бронирование слота клиентом.

Почему отдельная модель Booking:
- Один слот может быть забронирован несколькими клиентами
- Хранит информацию о конкретном бронировании (статус, оплата)
- Поддерживает гостевые бронирования (через guest_session_id)

Статусы бронирования:
- pending: создано, ожидает оплаты
- confirmed: оплачено и подтверждено
- cancelled: отменено (клиентом или автоматически)
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class BookingStatus:
    """Статусы бронирования."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingType:
    """Тип бронирования."""

    SINGLE = "single"
    COURSE = "course"


class Booking(Base):
    """
    Бронирование слота клиентом.
    
    Может быть создано:
    1. Зарегистрированным пользователем (user_id)
    2. Гостем (guest_session_id) - до активации через Magic Link
    
    После успешной оплаты статус меняется на CONFIRMED.
    """
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Связь со слотом (обязательно для SINGLE, для COURSE создаём по одному
    # Booking на каждый слот курса)
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.id"), nullable=False, index=True
    )

    # Тип бронирования и связь с услугой/заказом
    booking_type: Mapped[str] = mapped_column(
        String(20),
        default=BookingType.SINGLE,
        nullable=False,
        index=True,
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"), nullable=True, index=True
    )
    
    # Связь с пользователем (может быть NULL для гостевых бронирований)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    
    # Гостевая сессия (для бронирований до активации аккаунта)
    guest_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Информация о клиенте (для гостевых бронирований)
    guest_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Статус бронирования
    status: Mapped[str] = mapped_column(
        String(20),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Платежи (Stripe)
    checkout_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)  # Stripe Checkout Session ID
    payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)  # Stripe PaymentIntent ID
    payment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # succeeded, failed, etc.

    # Цена за конкретное посещение внутри курса (для аналитики и учёта).
    # Для одиночных бронирований может быть None или совпадать с ценой слота.
    unit_price_cents: Mapped[int | None] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)  # Когда было отменено
    
    # Связи
    slot: Mapped["Slot"] = relationship("Slot", back_populates="bookings")
    user: Mapped["User | None"] = relationship("User", back_populates="bookings")
    service: Mapped["Service | None"] = relationship(
        "Service",
        back_populates="bookings",
    )
    order: Mapped["Order | None"] = relationship(
        "Order",
        back_populates="bookings",
    )
    
    # Методы для проверки статуса (удобно использовать в коде)
    def is_confirmed(self) -> bool:
        """Проверка, подтверждено ли бронирование."""
        return self.status == BookingStatus.CONFIRMED
    
    def is_pending(self) -> bool:
        """Проверка, ожидает ли бронирование оплаты."""
        return self.status == BookingStatus.PENDING
    
    def is_cancelled(self) -> bool:
        """Проверка, отменено ли бронирование."""
        return self.status == BookingStatus.CANCELLED
