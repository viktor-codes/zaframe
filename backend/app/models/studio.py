"""
Модель Studio - студия/бизнес, предлагающий классы.

Почему отдельная модель Studio:
- Один владелец может иметь несколько студий
- Каждая студия имеет своё расписание и слоты
- Удобно для масштабирования (несколько локаций, разные направления)
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Studio(Base):
    """
    Студия/бизнес, предлагающий классы для бронирования.
    
    Принадлежит владельцу (User), имеет расписание и слоты.
    """
    __tablename__ = "studios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Связь с владельцем
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    # Основная информация
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Контакты студии
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Настройки
    is_active: Mapped[bool] = mapped_column(default=True)  # Активна ли студия
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Связи
    owner: Mapped["User"] = relationship("User", back_populates="studios")
    
    # Одна студия может иметь множество слотов
    slots: Mapped[list["Slot"]] = relationship(
        "Slot",
        back_populates="studio",
        cascade="all, delete-orphan"
    )
