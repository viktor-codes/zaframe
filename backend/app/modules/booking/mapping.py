"""Map Booking ORM entities to API response schemas."""

from __future__ import annotations

from app.core.exceptions import ValidationError
from app.models.booking import Booking
from app.models.user import User
from app.modules.booking.policies import is_own_booking
from app.modules.booking.schemas import (
    BookingCreatedResponse,
    BookingOwnerResponse,
    BookingSelfResponse,
)


def map_booking_for_user(
    booking: Booking, user: User
) -> BookingSelfResponse | BookingOwnerResponse:
    """
    Map ORM booking to the appropriate client response schema.

    Own bookings use BookingSelfResponse; studio-owner views use BookingOwnerResponse.
    """
    if is_own_booking(booking, user):
        return BookingSelfResponse.model_validate(booking)
    return BookingOwnerResponse.model_validate(booking)


def map_booking_created_response(booking: Booking) -> BookingCreatedResponse:
    """Map a newly created booking including the one-time guest checkout token."""
    if booking.access_token is None:
        raise ValidationError("Booking access token is missing")
    return BookingCreatedResponse(
        **BookingSelfResponse.model_validate(booking).model_dump(),
        access_token=booking.access_token,
    )
