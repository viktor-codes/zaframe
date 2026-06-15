"""
ScheduleTemplate — recurring rule for generating occurrences for a Service.
"""

from __future__ import annotations

from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin


class ScheduleTemplate(TimestampMixin, Base):
    """Wall-clock recurrence template (weekday + time + validity window)."""

    __tablename__ = "schedule_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)

    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    service: Mapped[Service] = relationship("Service", back_populates="schedule_templates")
    occurrences: Mapped[list[Occurrence]] = relationship(
        "Occurrence",
        back_populates="schedule_template",
    )
