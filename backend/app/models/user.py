"""
User model for application accounts.

Why email is the primary identifier:
- Unique for OTP authentication
- No username required, which keeps input short
- Email is already used for notifications

Why phone is optional:
- Not every user wants to share a phone number
- Email is enough for most flows
- Phone can be added later when needed
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.order import Order
    from app.models.refresh_token import RefreshToken
    from app.models.studio import Studio
    from app.models.studio_member import StudioMember


class UserRole(enum.StrEnum):
    """Global platform role. Studio access is handled by StudioMember."""

    USER = "user"
    STUDIO_OWNER = "studio_owner"
    ADMIN = "admin"


class User(TimestampMixin, Base):
    """
    Application user, either a customer or a studio owner.

    Created automatically after the first successful OTP verification.
    Can be linked to a studio as owner through Studio.owner_id.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Core profile data
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    marketing_consent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    role: Mapped[str] = mapped_column(
        Enum(
            "user",
            "studio_owner",
            "admin",
            name="user_role",
            create_constraint=False,
        ),
        nullable=False,
        default=UserRole.USER.value,
        server_default=UserRole.USER.value,
    )

    is_active: Mapped[bool] = mapped_column(default=True)

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    studios: Mapped[list[Studio]] = relationship(
        "Studio",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    studio_memberships: Mapped[list[StudioMember]] = relationship(
        "StudioMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
