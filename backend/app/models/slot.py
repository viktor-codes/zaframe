"""
Модель Slot - слот/класс для бронирования.

Почему Slot, а не Class:
- Class - зарезервированное слово в Python
- Slot более точно описывает временной слот для бронирования
- Избегаем конфликтов с встроенными типами

Структура:
- Slot привязан к Studio
- Имеет дату и время начала/окончания
- Имеет максимальное количество мест
- Может быть забронирован несколько раз (через Booking)
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class OccurrenceStatus:
    """Статус конкретного занятия (occurrence)."""

    ACTIVE = "active"
    CANCELLED = "cancelled"


class Slot(Base):
    """
    Слот/класс для бронирования.
    
    Представляет одно занятие (например, "Йога в 18:00, 5 февраля").
    Может быть забронирован несколькими клиентами (до max_capacity).
    """
    __tablename__ = "slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Связь со студией
    studio_id: Mapped[int] = mapped_column(
        ForeignKey("studios.id"), nullable=False, index=True
    )

    # Связь с услугой и шаблоном расписания
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id"), nullable=True, index=True
    )

    # Временные параметры
    start_time: Mapped[datetime] = mapped_column(
        nullable=False, index=True
    )  # Начало занятия
    end_time: Mapped[datetime] = mapped_column(nullable=False)  # Окончание занятия

    # Информация о классе
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # Название класса
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Вместимость
    max_capacity: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False
    )  # Максимальное количество мест

    # Цена (в центах, для Stripe)
    price_cents: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # Цена за одно место (drop‑in)
    course_price_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Опциональная цена "внутри курса" за это занятие

    # Статус
    is_active: Mapped[bool] = mapped_column(
        default=True
    )  # Активен ли слот для бронирования в принципе
    status: Mapped[str] = mapped_column(
        String(20),
        default=OccurrenceStatus.ACTIVE,
        nullable=False,
        index=True,
    )  # Доменный статус занятия (active/cancelled)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Связи
    studio: Mapped["Studio"] = relationship("Studio", back_populates="slots")
    service: Mapped["Service | None"] = relationship(
        "Service",
        back_populates="slots",
    )
    schedule: Mapped["Schedule | None"] = relationship(
        "Schedule",
        back_populates="slots",
    )

    # Один слот может иметь множество бронирований
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="slot",
        cascade="all, delete-orphan"
    )
    
    # Вычисляемое свойство: сколько мест занято
    # Будет реализовано через SQL запрос или property в схеме
