"""
Booking model — reservation of a seat on an Occurrence.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, column, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.occurrence import Occurrence
    from app.models.order import Order
    from app.models.payment import Payment
    from app.models.service import Service
    from app.models.user import User


class BookingStatus:
    """Booking lifecycle status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

    # WHY: only pending/confirmed block duplicate active bookings per occurrence+guest.
    ACTIVE_STATUSES: frozenset[str] = frozenset({PENDING, CONFIRMED})


class BookingType:
    """Booking granularity aligned with Service.type."""

    SINGLE = "single"
    COURSE = "course"


class Booking(TimestampMixin, Base):
    """Seat reservation on an occurrence (guest or registered user)."""

    __tablename__ = "bookings"
    __table_args__ = (
        # WHY: lower(guest_email) matches app-level ownership / duplicate checks.
        Index(
            "uq_bookings_occurrence_guest_email_active",
            "occurrence_id",
            func.lower(column("guest_email")),
            unique=True,
            postgresql_where=text("status IN ('pending', 'confirmed') AND guest_email IS NOT NULL"),
        ),
        Index(
            "uq_bookings_occurrence_user_id_active",
            "occurrence_id",
            "user_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'confirmed') AND user_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    occurrence_id: Mapped[int] = mapped_column(
        ForeignKey("occurrences.id"), nullable=False, index=True
    )

    booking_type: Mapped[str] = mapped_column(
        String(20),
        default=BookingType.SINGLE,
        nullable=False,
        index=True,
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    guest_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default=BookingStatus.PENDING, nullable=False, index=True
    )

    reserved_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    access_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    checkout_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    unit_price_cents: Mapped[int | None] = mapped_column(nullable=True)

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    no_show_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    occurrence: Mapped[Occurrence] = relationship("Occurrence", back_populates="bookings")
    user: Mapped[User | None] = relationship("User", back_populates="bookings")
    service: Mapped[Service | None] = relationship("Service", back_populates="bookings")
    order: Mapped[Order | None] = relationship("Order", back_populates="bookings")
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="booking")

    def is_confirmed(self) -> bool:
        return self.status == BookingStatus.CONFIRMED

    def is_pending(self) -> bool:
        return self.status == BookingStatus.PENDING

    def is_cancelled(self) -> bool:
        return self.status == BookingStatus.CANCELLED

    def is_expired(self) -> bool:
        return self.status == BookingStatus.EXPIRED

    def is_completed(self) -> bool:
        return self.status == BookingStatus.COMPLETED

    def is_no_show(self) -> bool:
        return self.status == BookingStatus.NO_SHOW
