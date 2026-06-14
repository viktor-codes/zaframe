"""
OTP code model for email-based passwordless authentication.

WHY separate table (not fields on User):
- Ephemeral credential with attempts counter and expiry
- Rate limiting via (email, created_at) queries
- Audit trail without polluting the user profile
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import TimestampMixin


class OTPCode(TimestampMixin, Base):
    """One-time password sent to email for sign-in or account creation."""

    __tablename__ = "otp_codes"
    __table_args__ = (
        Index("ix_otp_codes_email_expires_at", "email", "expires_at"),
        Index("ix_otp_codes_email_created_at", "email", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # Used only when verify creates a new User

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    request_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    def is_active(self, *, now: datetime) -> bool:
        """True when the code is unused and not expired."""
        return self.used_at is None and self.expires_at > now
