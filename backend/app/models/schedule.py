"""
Модель Schedule — шаблон расписания для услуги (Service).

Schedule описывает:
- день недели (0-6, Пн-Вс)
- время начала
- период действия (valid_from / valid_to)

Конкретные занятия создаются как Slot (occurrence) и могут ссылаться
на Schedule через внешние ключи.
"""
from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import ForeignKey, Integer, Time, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Schedule(Base):
    """Шаблон повторяющегося расписания для услуги."""

    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"), nullable=False, index=True
    )

    # День недели 0-6 (Пн-Вс)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)

    # Время начала занятия (без даты)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Период действия расписания
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Связи
    service: Mapped["Service"] = relationship("Service", back_populates="schedules")
    slots: Mapped[list["Slot"]] = relationship(
        "Slot",
        back_populates="schedule",
    )

