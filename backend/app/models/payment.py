"""Payment ledger models for Stripe payments and refunds."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.order import Order


class PaymentStatus:
    """Payment status values stored in the local ledger."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    FAILED = "failed"


class PaymentProvider:
    """Payment provider identifiers."""

    STRIPE = "stripe"


class RefundStatus:
    """Refund status values stored in the local ledger."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(TimestampMixin, Base):
    """Local ledger row for one external payment."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "(booking_id IS NOT NULL) <> (order_id IS NOT NULL)",
            name="ck_payments_exactly_one_parent",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id"),
        nullable=True,
        index=True,
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )
    stripe_checkout_session_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(30),
        default=PaymentProvider.STRIPE,
        nullable=False,
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    booking: Mapped[Booking | None] = relationship("Booking", back_populates="payments")
    order: Mapped[Order | None] = relationship("Order", back_populates="payments")
    refunds: Mapped[list[Refund]] = relationship(
        "Refund",
        back_populates="payment",
        cascade="all, delete-orphan",
    )


class Refund(Base):
    """Local ledger row for one external refund."""

    __tablename__ = "refunds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False, index=True)
    stripe_refund_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=RefundStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    payment: Mapped[Payment] = relationship("Payment", back_populates="refunds")
