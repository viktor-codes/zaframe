"""
Модель Service — описание услуги/класса, который может продаваться как
разовое занятие (drop‑in) или как курс.

Service не является конкретным занятием во времени — для этого есть
occurrence'ы (модель Slot), которые ссылаются на Service.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class ServiceType:
    """Тип услуги."""

    SINGLE_CLASS = "single_class"
    COURSE = "course"


class Service(Base):
    """
    Услуга, предлагаемая студией.

    Примеры:
    - "Yoga for Couples"
    - "Adult Dance Class (6-week course)"
    """

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Привязка к студии
    studio_id: Mapped[int] = mapped_column(
        ForeignKey("studios.id"), nullable=False, index=True
    )

    # Основная информация
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Тип услуги: разовое занятие или курс
    type: Mapped[str] = mapped_column(
        String(20),
        default=ServiceType.SINGLE_CLASS,
        nullable=False,
        index=True,
    )

    # Настройки длительности и вместимости
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Цены в центах (Stripe‑френдли)
    price_single_cents: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # цена за одно занятие (drop‑in)
    price_course_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # цена за весь курс

    # Параметры overbooking‑логики по умолчанию для этой услуги.
    # Могут отличаться для разных типов классов (йога vs латина).
    soft_limit_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    hard_limit_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.5,
    )
    max_overbooked_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.3,
    )

    # Активна ли услуга
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Связи
    studio: Mapped["Studio"] = relationship("Studio", back_populates="services")
    slots: Mapped[list["Slot"]] = relationship(
        "Slot",
        back_populates="service",
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="service",
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="service",
    )

    # === Бизнес-логика вместимости ===
    def get_capacity_status(
        self,
        *,
        max_capacity: int,
        current_bookings: int,
        requested: int = 1,
    ) -> str | None:
        """
        Возвращает статус заполненности для заданного количества мест.

        Используется для реализации soft/hard лимитов и overbooking-логики.

        Возвращаемые значения:
        - "HARD_LIMIT_REACHED" — превышен жёсткий предел
        - "SOFT_LIMIT_REACHED" — превышен мягкий предел
        - None — в пределах soft‑лимита
        """
        total = current_bookings + requested
        soft_limit = int(max_capacity * self.soft_limit_ratio)
        hard_limit = int(max_capacity * self.hard_limit_ratio)

        if total > hard_limit:
            return "HARD_LIMIT_REACHED"
        if total > soft_limit:
            return "SOFT_LIMIT_REACHED"
        return None

