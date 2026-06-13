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

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin


class SlotStatus:
    """Статусы слота (занятия)."""

    ACTIVE = "active"
    CANCELLED = "cancelled"


class Slot(TimestampMixin, Base):
    """
    Слот/класс для бронирования.

    Представляет одно занятие (например, "Йога в 18:00, 5 февраля").
    Может быть забронирован несколькими клиентами (до max_capacity).
    """

    __tablename__ = "slots"
    __table_args__ = (
        Index(
            "idx_slots_studio_service_start_time",
            "studio_id",
            "service_id",
            "start_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Связь со студией
    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.id"), nullable=False, index=True)

    # Связь с услугой и шаблоном расписания
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedules.id"), nullable=True, index=True
    )

    # Временные параметры (UTC)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )  # Начало занятия
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )  # Окончание занятия

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

    # Статус занятия (active/cancelled)
    status: Mapped[str] = mapped_column(
        String(20),
        default=SlotStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Связи
    studio: Mapped[Studio] = relationship("Studio", back_populates="slots")
    service: Mapped[Service | None] = relationship(
        "Service",
        back_populates="slots",
    )
    schedule: Mapped[Schedule | None] = relationship(
        "Schedule",
        back_populates="slots",
    )

    # Один слот может иметь множество бронирований
    bookings: Mapped[list[Booking]] = relationship(
        "Booking", back_populates="slot", cascade="all, delete-orphan"
    )

    def is_bookable(self) -> bool:
        """Слот доступен для новых бронирований."""
        return self.status == SlotStatus.ACTIVE

    def is_cancelled(self) -> bool:
        """Занятие отменено (occurrence cancelled)."""
        return self.status == SlotStatus.CANCELLED
