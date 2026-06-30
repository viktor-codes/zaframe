"""
Order model for paying for one or more classes.

Order is the parent for one or more Booking rows:
- it may be absent for single bookings in legacy mode
- for courses, one Order aggregates all bookings across course occurrences
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.payment import Payment
    from app.models.service import Service
    from app.models.studio import Studio
    from app.models.user import User


class OrderStatus:
    """Order statuses."""

    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REFUNDED = "refunded"
    MANUAL_REVIEW = "manual_review"


class Order(TimestampMixin, Base):
    """Payment order for a single service or course."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Studio and service links
    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.id"), nullable=False, index=True)
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )

    # Buyer identity
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guest_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Payment details
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="eur", nullable=False)
    application_fee_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checkout_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    status: Mapped[str] = mapped_column(
        String(20),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )

    access_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Relationships
    studio: Mapped[Studio] = relationship("Studio", back_populates="orders")
    service: Mapped[Service | None] = relationship("Service", back_populates="orders")
    user: Mapped[User | None] = relationship("User", back_populates="orders")
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="order")
