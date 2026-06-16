"""
Pydantic schemas for Booking model.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, computed_field

from app.models.booking import BookingType
from app.modules.catalog.occurrence import OccurrenceResponse
from app.modules.catalog.studio.schemas import StudioResponse
from app.modules.identity import UserPublic


class BookingBase(BaseModel):
    """Base booking fields."""

    occurrence_id: int = Field(..., description="Occurrence ID to book")

    model_config = ConfigDict(populate_by_name=True)


class BookingCreate(BookingBase):
    """
    Guest booking create payload.

    Used before OTP verify; user_id is attached after verification.
    """

    guest_name: str = Field(..., min_length=1, max_length=100, description="Guest name")
    guest_email: EmailStr = Field(..., description="Guest email")
    guest_phone: str | None = Field(None, max_length=20, description="Guest phone (optional)")
    booking_type: str = Field(
        default=BookingType.SINGLE,
        description="Booking type: single or course",
    )
    service_id: int | None = Field(
        None,
        description="Service ID (required for course bookings)",
    )


class BookingCreateAuthenticated(BookingBase):
    """Authenticated user booking create payload (user_id from token)."""

    pass


class BookingResponseBase(BookingBase):
    """
    Shared booking response fields for Self and Owner perspectives.

    Stripe checkout_session_id and payment_intent_id are intentionally excluded.
    """

    id: int
    user_id: int | None
    status: str
    reserved_until: AwareDatetime | None = Field(
        None,
        description="UTC timestamp until which a pending booking reserves occurrence capacity",
    )
    payment_status: str | None = Field(
        None,
        description="Payment status (no internal Stripe IDs)",
    )
    created_at: AwareDatetime
    updated_at: AwareDatetime
    cancelled_at: AwareDatetime | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @computed_field
    @property
    def is_guest_booking(self) -> bool:
        """True when booking was created without a linked user account."""
        return self.user_id is None


class BookingSelfResponse(BookingResponseBase):
    """Self perspective: booking owner (guest or authenticated user)."""

    guest_name: str | None = Field(None, description="Name on the booking")
    guest_email: str | None = Field(None, description="Email on the booking")
    guest_phone: str | None = Field(None, description="Phone on the booking")


class BookingCreatedResponse(BookingSelfResponse):
    """Create response — includes one-time guest checkout token (not in lists or GET)."""

    access_token: str = Field(
        ...,
        description="Guest checkout token; required for unauthenticated payment",
    )


class BookingOwnerResponse(BookingResponseBase):
    """Owner perspective: studio staff view with guest contact details."""

    guest_name: str | None = Field(None, description="Guest name")
    guest_email: str | None = Field(None, description="Guest email for contact")
    guest_phone: str | None = Field(None, description="Guest phone for contact")


class BookingWithOccurrence(BookingOwnerResponse):
    """Owner perspective with nested occurrence."""

    occurrence: OccurrenceResponse = Field(
        ...,
        description="Occurrence details",
        validation_alias="occurrence",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BookingWithUser(BookingOwnerResponse):
    """Owner perspective with nested user profile."""

    user: UserPublic | None = Field(None, description="Linked user profile")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BookingSelfListItem(BookingSelfResponse):
    """
    Self perspective list item for /bookings/my.

    Nested occurrence + studio to avoid N+1 on the frontend.
    """

    occurrence: OccurrenceResponse = Field(
        ...,
        description="Occurrence details",
        validation_alias="occurrence",
    )
    studio: StudioResponse = Field(..., description="Studio details")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class BookingCancel(BaseModel):
    """Cancel booking request."""

    reason: str | None = Field(None, max_length=500, description="Cancellation reason")
