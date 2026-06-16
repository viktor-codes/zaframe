"""Course booking DTO → API response schemas."""

from app.modules.booking import BookingSelfResponse
from app.modules.booking.order import (
    CourseAvailabilityResult,
    CourseBookingPreviewItem,
    CourseBookingResponse,
    CourseBookingResultDTO,
    OrderResponse,
)
from app.modules.catalog.service import CourseAvailabilityDTO


def map_course_availability(dto: CourseAvailabilityDTO) -> CourseAvailabilityResult:
    return CourseAvailabilityResult(
        can_book=dto.can_book,
        requires_warning=dto.requires_warning,
        hard_block=dto.hard_block,
        overbooked_occurrences=[
            CourseBookingPreviewItem(
                occurrence_id=item.occurrence_id,
                start_time=item.start_time,
                max_capacity=item.max_capacity,
                confirmed_count=item.confirmed_count,
                pending_count=item.pending_count,
                total_after_booking=item.total_after_booking,
                is_over_soft_limit=item.is_over_soft_limit,
                is_over_hard_limit=item.is_over_hard_limit,
            )
            for item in dto.overbooked_occurrences
        ],
        message=dto.message,
    )


def map_course_booking_result(dto: CourseBookingResultDTO) -> CourseBookingResponse:
    if dto.order.access_token is None:
        raise ValueError("Order access token is missing")
    return CourseBookingResponse(
        order=OrderResponse.model_validate(dto.order),
        bookings=[BookingSelfResponse.model_validate(booking) for booking in dto.bookings],
        availability=map_course_availability(dto.availability),
        access_token=dto.order.access_token,
    )
