from typing import TYPE_CHECKING

from app.modules.booking.order.dto import CourseBookingInput, CourseBookingResultDTO
from app.modules.booking.order.repository import OrderRepository
from app.modules.booking.order.schemas import (
    CourseAvailabilityResult,
    CourseBookingCreate,
    CourseBookingPreviewItem,
    CourseBookingResponse,
    OrderBase,
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
    "OrderRepository",
    "OrderResponse",
    "create_course_booking",
]

if TYPE_CHECKING:
    from app.modules.booking.order.service import create_course_booking


def __getattr__(name: str):
    if name == "create_course_booking":
        from app.modules.booking.order import service

        return service.create_course_booking
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
