"""
Occurrence model — a concrete bookable session in time.

Generated from ScheduleTemplate rules or created manually; referenced by Booking.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.schedule_template import ScheduleTemplate
    from app.models.service import Service
    from app.models.studio import Studio
    from app.models.studio_member import StudioMember


class OccurrenceStatus:
    """Occurrence lifecycle status."""

    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Occurrence(TimestampMixin, Base):
    """One schedulable session instance (e.g. Yoga on 5 Feb at 18:00)."""

    __tablename__ = "occurrences"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'cancelled', 'completed')",
            name="ck_occurrences_status",
        ),
        Index(
            "idx_occurrences_studio_service_start_time",
            "studio_id",
            "service_id",
            "start_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.id"), nullable=False, index=True)

    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)
    schedule_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_templates.id"), nullable=True, index=True
    )
    instructor_id: Mapped[int | None] = mapped_column(
        ForeignKey("studio_members.id"), nullable=True, index=True
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    max_capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    course_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        default=OccurrenceStatus.SCHEDULED,
        server_default=OccurrenceStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    studio: Mapped[Studio] = relationship("Studio", back_populates="occurrences")
    service: Mapped[Service] = relationship(
        "Service",
        back_populates="occurrences",
    )
    schedule_template: Mapped[ScheduleTemplate | None] = relationship(
        "ScheduleTemplate",
        back_populates="occurrences",
    )
    instructor: Mapped[StudioMember | None] = relationship(
        "StudioMember",
        back_populates="assigned_occurrences",
    )
    bookings: Mapped[list[Booking]] = relationship(
        "Booking", back_populates="occurrence", cascade="all, delete-orphan"
    )

    def is_bookable(self) -> bool:
        """Occurrence accepts new bookings."""
        return self.status == OccurrenceStatus.SCHEDULED

    def is_cancelled(self) -> bool:
        """Occurrence was cancelled."""
        return self.status == OccurrenceStatus.CANCELLED

    def is_completed(self) -> bool:
        """Occurrence has been completed and preserved for history."""
        return self.status == OccurrenceStatus.COMPLETED
