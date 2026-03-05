"""
Модель GuestSession - временная сессия для гостевых бронирований.

Почему отдельная модель:
- Хранит данные гостя до активации аккаунта через Magic Link
- Позволяет привязать бронирования к email даже без аккаунта
- Упрощает процесс "гостевого checkout"

Жизненный цикл:
1. Создаётся при первом бронировании (если пользователь не залогинен)
2. Хранит временные данные (email, name, phone)
3. После Magic Link → данные переносятся в User, сессия удаляется
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class GuestSession(Base):
    """
    Временная сессия для гостевых бронирований.
    
    Используется для хранения данных клиента до активации аккаунта через Magic Link.
    После активации данные переносятся в User, сессия удаляется.
    """
    __tablename__ = "guest_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Уникальный идентификатор сессии (хранится в cookie)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Данные гостя
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Срок действия сессии (по умолчанию 30 дней, хранится в UTC)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Timestamps (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Метод для проверки истечения сессии
    def is_expired(self) -> bool:
        """Проверка, истекла ли сессия."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @classmethod
    def create_default_expires_at(cls) -> datetime:
        """Создаёт дату истечения по умолчанию (30 дней)."""
        return datetime.now(timezone.utc) + timedelta(days=30)
