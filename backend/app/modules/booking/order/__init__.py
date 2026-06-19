from typing import TYPE_CHECKING

from app.modules.booking.order.dto import CourseBookingInput, CourseBookingResultDTO
from app.modules.booking.order.repository import OrderRepository
from app.modules.booking.order.schemas import (
    CourseAvailabilityResult,
    CourseBookingCreate,
    CourseBookingPreviewItem,
    CourseBookingResponse,
    OrderBase,
    OrderBookingSummary,
    OrderListItem,
    OrderResponse,
)

__all__ = [
    "CourseAvailabilityResult",
    "CourseBookingCreate",
    "CourseBookingInput",
    "CourseBookingPreviewItem",
    "CourseBookingResponse",
    "CourseBookingResultDTO",
    "OrderBase",
    "OrderBookingSummary",
    "OrderListItem",
    "OrderRepository",
    "OrderResponse",
    "create_course_booking",
    "get_my_orders",
    "get_owner_orders",
]

if TYPE_CHECKING:
    from app.modules.booking.order.service import (
        create_course_booking,
        get_my_orders,
        get_owner_orders,
    )


def __getattr__(name: str):
    if name in ("create_course_booking", "get_my_orders", "get_owner_orders"):
        from app.modules.booking.order import service

        return {
            "create_course_booking": service.create_course_booking,
            "get_my_orders": service.get_my_orders,
            "get_owner_orders": service.get_owner_orders,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
