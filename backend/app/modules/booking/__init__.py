import importlib
from typing import TYPE_CHECKING

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
    "check_in_booking",
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
    "mark_booking_no_show",
]

_SERVICE_FUNCTION_MODULES: dict[str, str] = {
    "DUPLICATE_BOOKING_MESSAGE": "app.modules.booking.persistence",
    "attach_guest_bookings": "app.modules.booking.queries",
    "cancel_booking": "app.modules.booking.service",
    "check_in_booking": "app.modules.booking.service",
    "complete_past_confirmed": "app.modules.booking.lifecycle",
    "create_booking": "app.modules.booking.service",
    "expire_stale_pending": "app.modules.booking.lifecycle",
    "get_booking_for_user_or_raise": "app.modules.booking.queries",
    "get_bookings": "app.modules.booking.queries",
    "get_my_bookings": "app.modules.booking.queries",
    "get_owner_bookings": "app.modules.booking.queries",
    "get_owner_bookings_count": "app.modules.booking.queries",
    "map_booking_created_response": "app.modules.booking.mapping",
    "map_booking_for_user": "app.modules.booking.mapping",
    "mark_booking_no_show": "app.modules.booking.service",
}

if TYPE_CHECKING:
    from app.modules.booking.lifecycle import complete_past_confirmed, expire_stale_pending
    from app.modules.booking.mapping import map_booking_created_response, map_booking_for_user
    from app.modules.booking.persistence import DUPLICATE_BOOKING_MESSAGE
    from app.modules.booking.queries import (
        attach_guest_bookings,
        get_booking_for_user_or_raise,
        get_bookings,
        get_my_bookings,
        get_owner_bookings,
        get_owner_bookings_count,
    )
    from app.modules.booking.service import (
        cancel_booking,
        check_in_booking,
        create_booking,
        mark_booking_no_show,
    )


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading BookingRepository from this package.
    module_path = _SERVICE_FUNCTION_MODULES.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_path)
    return getattr(module, name)
