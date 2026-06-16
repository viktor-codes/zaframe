from app.modules.booking.policies import can_access_booking, is_own_booking
from app.modules.booking.repository import BookingRepository
from app.modules.booking.schemas import (
    BookingCreate,
    BookingCreatedResponse,
    BookingOwnerResponse,
    BookingSelfListItem,
    BookingSelfResponse,
)

__all__ = [
    "BookingCreate",
    "BookingCreatedResponse",
    "BookingOwnerResponse",
    "BookingRepository",
    "BookingSelfListItem",
    "BookingSelfResponse",
    "DUPLICATE_BOOKING_MESSAGE",
    "attach_guest_bookings",
    "can_access_booking",
    "cancel_booking",
    "complete_past_confirmed",
    "create_booking",
    "expire_stale_pending",
    "get_booking_for_user_or_raise",
    "get_bookings",
    "get_my_bookings",
    "get_owner_bookings",
    "get_owner_bookings_count",
    "is_own_booking",
    "map_booking_created_response",
    "map_booking_for_user",
]

_SERVICE_FUNCTIONS = (
    "DUPLICATE_BOOKING_MESSAGE",
    "attach_guest_bookings",
    "cancel_booking",
    "complete_past_confirmed",
    "create_booking",
    "expire_stale_pending",
    "get_booking_for_user_or_raise",
    "get_bookings",
    "get_my_bookings",
    "get_owner_bookings",
    "get_owner_bookings_count",
    "map_booking_created_response",
    "map_booking_for_user",
)


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading BookingRepository from this package.
    if name in _SERVICE_FUNCTIONS:
        from app.modules.booking import service

        return getattr(service, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
