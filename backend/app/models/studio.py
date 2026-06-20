"""
Модель Studio - студия/бизнес, предлагающий классы.

Почему отдельная модель Studio:
- Один владелец может иметь несколько студий
- Каждая студия имеет своё расписание и слоты
- Удобно для масштабирования (несколько локаций, разные направления)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.occurrence import Occurrence
    from app.models.order import Order
    from app.models.service import Service
    from app.models.studio_member import StudioMember
    from app.models.user import User


class Studio(TimestampMixin, Base):
    """
    Студия/бизнес, предлагающий классы для бронирования.

    Принадлежит владельцу (User), имеет расписание и слоты.
    """

    __tablename__ = "studios"
    __table_args__ = (
        CheckConstraint(
            "cancel_before_hours >= 0",
            name="ck_studios_cancel_before_hours_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Связь с владельцем
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Основная информация
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Публичный slug для URL (например, /studios/yoga-hub-berlin).
    # Делаем nullable для обратной совместимости, позже можно сделать обязательным.
    slug: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Контакты студии
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    amenities: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # IANA timezone for schedule wall-clock and local display (e.g. Europe/Berlin).
    # DB default 'UTC' is for dev/SQL only; StudioCreate API requires explicit value.
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
        server_default="UTC",
    )

    # Настройки
    is_active: Mapped[bool] = mapped_column(default=True)  # Активна ли студия
    cancel_before_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
        server_default="24",
    )

    # Stripe Connect payout state
    stripe_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_charges_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    stripe_payouts_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    stripe_onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    stripe_onboarding_url_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Связи
    owner: Mapped[User] = relationship("User", back_populates="studios")
    members: Mapped[list[StudioMember]] = relationship(
        "StudioMember",
        back_populates="studio",
        cascade="all, delete-orphan",
    )

    # Одна студия может иметь множество слотов
    occurrences: Mapped[list[Occurrence]] = relationship(
        "Occurrence", back_populates="studio", cascade="all, delete-orphan"
    )
    # Одна студия может иметь множество услуг
    services: Mapped[list[Service]] = relationship(
        "Service",
        back_populates="studio",
        cascade="all, delete-orphan",
    )
    # Заказы, оформленные в этой студии
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="studio",
        cascade="all, delete-orphan",
    )
