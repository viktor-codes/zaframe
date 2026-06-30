"""
Service model for an offering that can be sold as a single drop-in class or a course.

Service is not a concrete class in time. Occurrence rows represent scheduled
instances and point back to Service.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.occurrence import Occurrence
    from app.models.order import Order
    from app.models.schedule_template import ScheduleTemplate
    from app.models.studio import Studio


class ServiceCategory(enum.StrEnum):
    """Service category for search and filtering."""

    YOGA = "yoga"
    BOXING = "boxing"
    DANCE = "dance"
    HIIT = "hiit"
    PILATES = "pilates"
    MARTIAL_ARTS = "martial_arts"
    STRENGTH = "strength"


class ServiceType:
    """Sellable offering type (aligned with BookingType)."""

    SINGLE = "single"
    COURSE = "course"


class ServiceVisibility:
    """Product lifecycle state for storefront and dashboard behavior."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Service(TimestampMixin, Base):
    """
    Service offered by a studio.

    Examples:
    - "Yoga for Couples"
    - "Adult Dance Class (6-week course)"
    """

    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('draft', 'published', 'archived')",
            name="ck_services_visibility",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Studio link
    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.id"), nullable=False, index=True)

    # Core information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Service type: single drop-in class or course
    type: Mapped[str] = mapped_column(
        String(20),
        default=ServiceType.SINGLE,
        nullable=False,
        index=True,
    )

    # Service category (PostgreSQL enum service_category in the database).
    # Explicit string values avoid name/value drift when reading and writing.
    category: Mapped[str] = mapped_column(
        Enum(
            "yoga",
            "boxing",
            "dance",
            "hiit",
            "pilates",
            "martial_arts",
            "strength",
            name="service_category",
            create_constraint=False,
        ),
        nullable=False,
        default=ServiceCategory.YOGA.value,
        index=True,
    )

    # Duration and capacity settings
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Prices in cents for Stripe-friendly minor units
    price_single_cents: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # price for one drop-in class
    price_course_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # price for the full course

    # Default overbooking parameters for this service.
    # They can differ by class type, e.g. yoga vs latin dance.
    soft_limit_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    hard_limit_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.5,
    )
    max_overbooked_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.3,
    )

    # Tags for additional classification, e.g. "beginner" or "evening"
    tags: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    visibility: Mapped[str] = mapped_column(
        String(20),
        default=ServiceVisibility.PUBLISHED,
        server_default=ServiceVisibility.PUBLISHED,
        nullable=False,
        index=True,
    )

    # Legacy operational flag; visibility is the product lifecycle source of truth.
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    studio: Mapped[Studio] = relationship("Studio", back_populates="services")
    occurrences: Mapped[list[Occurrence]] = relationship(
        "Occurrence",
        back_populates="service",
    )
    schedule_templates: Mapped[list[ScheduleTemplate]] = relationship(
        "ScheduleTemplate",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="service",
    )
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="service",
    )

    def is_publicly_visible(self) -> bool:
        """Service can appear in anonymous catalog/search surfaces."""
        return self.is_active and self.visibility == ServiceVisibility.PUBLISHED

    def is_bookable(self) -> bool:
        """Service allows creating new bookings through its occurrences."""
        return self.is_publicly_visible()

    # === Capacity business logic ===
    def get_capacity_status(
        self,
        *,
        max_capacity: int,
        current_bookings: int,
        requested: int = 1,
    ) -> str | None:
        """
        Return the capacity status for the requested number of seats.

        Used to implement soft/hard limits and overbooking logic.

        Returns:
        - "HARD_LIMIT_REACHED" when the hard limit is exceeded
        - "SOFT_LIMIT_REACHED" when the soft limit is exceeded
        - None when within the soft limit
        """
        total = current_bookings + requested
        soft_limit = int(max_capacity * self.soft_limit_ratio)
        hard_limit = int(max_capacity * self.hard_limit_ratio)

        if total > hard_limit:
            return "HARD_LIMIT_REACHED"
        if total > soft_limit:
            return "SOFT_LIMIT_REACHED"
        return None
