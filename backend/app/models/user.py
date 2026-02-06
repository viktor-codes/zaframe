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
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
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
    magic_link_token: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Токен для Magic Link
    magic_link_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)  # Срок действия токена
    
    # Timestamps
    # Используем server_default для автоматической установки времени на стороне БД
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Связи
    # Один пользователь может быть владельцем нескольких студий
    studios: Mapped[list["Studio"]] = relationship(
        "Studio",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    # Один пользователь может иметь множество бронирований
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan"
    )
