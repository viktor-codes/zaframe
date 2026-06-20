"""
Модель User - пользователь системы.

Почему email как основной идентификатор:
- Уникальность для OTP-аутентификации
- Не требует username (меньше полей для ввода)
- Email уже используется для уведомлений

Почему phone опциональный:
- Не все хотят делиться телефоном
- Email достаточно для большинства случаев
- Можно добавить позже при необходимости
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.order import Order
    from app.models.refresh_token import RefreshToken
    from app.models.studio import Studio
    from app.models.studio_member import StudioMember


class UserRole(enum.StrEnum):
    """Global platform role. Studio access is handled by StudioMember."""

    USER = "user"
    STUDIO_OWNER = "studio_owner"
    ADMIN = "admin"


class User(TimestampMixin, Base):
    """
    Пользователь системы (клиент или владелец студии).

    Создаётся автоматически при первой успешной OTP-верификации.
    Может быть привязан к студии как владелец (через Studio.owner_id).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Основные данные
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    marketing_consent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    role: Mapped[str] = mapped_column(
        Enum(
            "user",
            "studio_owner",
            "admin",
            name="user_role",
            create_constraint=False,
        ),
        nullable=False,
        default=UserRole.USER.value,
        server_default=UserRole.USER.value,
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Связи
    studios: Mapped[list[Studio]] = relationship(
        "Studio",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    studio_memberships: Mapped[list[StudioMember]] = relationship(
        "StudioMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
