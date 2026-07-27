"""
Idempotency ledger for POST /bookings (single + course create).

WHY: double-submit / multi-tab retries with the same Idempotency-Key must return
the original hold instead of consuming another seat.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class BookingIdempotencyKey(Base):
    """Maps a client Idempotency-Key to the created booking or order."""

    __tablename__ = "booking_idempotency_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    resource_id: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
