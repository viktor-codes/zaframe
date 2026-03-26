"""
Модель User - пользователь системы.

Почему email как основной идентификатор:
- Уникальность для Magic Link аутентификации
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

    Создаётся автоматически при первом использовании Magic Link.
    Может быть привязан к студии как владелец (через Studio.owner_id).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Основные данные
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Аутентификация (для Magic Link)
    is_active: Mapped[bool] = mapped_column(default=True)  # Аккаунт активирован через Magic Link
    magic_link_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )  # Хэш токена для Magic Link
    magic_link_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )  # Срок действия токена (UTC)

    # Временные поля авторизации
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Связи
    # Один пользователь может быть владельцем нескольких студий
    studios: Mapped[list[Studio]] = relationship(
        "Studio",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    # Один пользователь может иметь множество бронирований
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # И множество заказов
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # И множество refresh-токенов (сессий)
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
