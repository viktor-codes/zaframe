"""
Order and course-purchase schemas.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field

from app.modules.booking.schemas import BookingSelfResponse


class OrderBase(BaseModel):
    """Base order fields."""

    total_amount_cents: int = Field(..., ge=0, description="Order total in cents")
    currency: str = Field("eur", max_length=10, description="Order currency")


class OrderResponse(OrderBase):
    """Order API response."""

    id: int
    studio_id: int
    service_id: int | None
    user_id: int | None
    guest_email: EmailStr | None
    guest_name: str | None
    guest_phone: str | None = Field(None, description="Guest phone for contact")
    status: str = Field(..., description="Order status")
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class CourseBookingPreviewItem(BaseModel):
    """Single occurrence preview when checking course availability."""

    occurrence_id: int
    start_time: AwareDatetime
    max_capacity: int
    confirmed_count: int
    pending_count: int
    total_after_booking: int
    is_over_soft_limit: bool
    is_over_hard_limit: bool


class CourseAvailabilityResult(BaseModel):
    """Course availability check for purchase UI warnings."""

    can_book: bool = Field(..., description="Whether the course can be purchased")
    requires_warning: bool = Field(
        ...,
        description="Whether the UI should show an overbooking warning",
    )
    hard_block: bool = Field(
        ...,
        description="Whether purchase is blocked by hard capacity limit",
    )
    overbooked_occurrences: list[CourseBookingPreviewItem] = Field(
        default_factory=list,
        description="Occurrences that would be overbooked after purchase",
    )
    message: str | None = Field(
        None,
        description="Human-readable message for the UI",
    )


class CourseBookingCreate(BaseModel):
    """Guest course purchase request."""

    service_id: int = Field(..., description="Course service ID")
    guest_name: str = Field(..., min_length=1, max_length=100)
    guest_email: EmailStr = Field(..., description="Guest email")
    guest_phone: str | None = Field(None, max_length=20)


class CourseBookingResponse(BaseModel):
    """Response after creating a course order and bookings."""

    order: OrderResponse
    bookings: list[BookingSelfResponse]
    availability: CourseAvailabilityResult | None = None
    access_token: str = Field(
        ...,
        description="Order checkout token; required for unauthenticated payment",
    )
