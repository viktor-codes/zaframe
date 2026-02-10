"""
Модель Order — заказ на оплату набора занятий.

Order — это "родитель" для одного или нескольких Booking:
- для разового бронирования может быть не создан (legacy режим)
- для курса один Order агрегирует все бронирования по слотам курса
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class OrderStatus:
    """Статусы заказа."""

    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base):
    """Заказ на оплату услуги (single или курс)."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Привязка к студии и услуге
    studio_id: Mapped[int] = mapped_column(
        ForeignKey("studios.id"), nullable=False, index=True
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )

    # Кто купил
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guest_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Финансы
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="eur", nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Связи
    studio: Mapped["Studio"] = relationship("Studio", back_populates="orders")
    service: Mapped["Service | None"] = relationship("Service", back_populates="orders")
    user: Mapped["User | None"] = relationship("User", back_populates="orders")
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="order",
        cascade="all, delete-orphan",
    )

