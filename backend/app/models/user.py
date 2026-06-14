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

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin


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

    is_active: Mapped[bool] = mapped_column(default=True)

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Связи
    studios: Mapped[list[Studio]] = relationship(
        "Studio",
        back_populates="owner",
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
