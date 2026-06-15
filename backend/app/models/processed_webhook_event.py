"""
Stripe webhook idempotency ledger.

WHY separate table: Stripe may deliver the same event.id more than once;
booking/order status alone is not enough to skip duplicate side effects safely.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ProcessedWebhookEvent(Base):
    """One row per successfully processed Stripe event.id."""

    __tablename__ = "processed_webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column("type", String(128), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
