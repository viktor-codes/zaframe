"""ORM / service DTO → Pydantic response schemas (API layer only)."""

from app.schemas import (
    BookingSelfResponse,
    CourseAvailabilityResult,
    CourseBookingPreviewItem,
    CourseBookingResponse,
    OrderResponse,
    PublicService,
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
    StudioPublicResponse,
)
from app.services.dto import (
    CourseAvailabilityDTO,
    CourseBookingResultDTO,
    PublicServiceDTO,
    ServiceAvailabilityDTO,
    StudioPublicDTO,
)


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


def _map_public_service(dto: PublicServiceDTO) -> PublicService:
    availability: PublicService.Availability | None = None
    if dto.availability is not None:
        availability = PublicService.Availability(
            can_book=dto.availability.can_book,
            total_remaining_capacity=dto.availability.total_remaining_capacity,
            requires_warning=dto.availability.requires_warning,
            overbooked_dates=dto.availability.overbooked_dates,
        )

    return PublicService(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        type=dto.type,
        duration_minutes=dto.duration_minutes,
        max_capacity=dto.max_capacity,
        price_single_cents=dto.price_single_cents,
        price_course_cents=dto.price_course_cents,
        cover_image_url=dto.cover_image_url,
        next_term_start=dto.next_term_start,
        term_end=dto.term_end,
        occurrences_count=dto.occurrences_count,
        availability=availability,
    )


def map_studio_public(dto: StudioPublicDTO) -> StudioPublicResponse:
    return StudioPublicResponse(
        id=dto.id,
        name=dto.name,
        slug=dto.slug,
        description=dto.description,
        services=[_map_public_service(service) for service in dto.services],
    )


def map_service_availability(dto: ServiceAvailabilityDTO) -> ServiceAvailabilityResponse:
    return ServiceAvailabilityResponse(
        service_id=dto.service_id,
        can_book=dto.can_book,
        requires_warning=dto.requires_warning,
        warning_message=dto.warning_message,
        schedule_details=[
            ServiceAvailabilityScheduleItem(
                date=item.date,
                is_overbooked=item.is_overbooked,
                remaining=item.remaining,
                overbooking_status=item.overbooking_status,
            )
            for item in dto.schedule_details
        ],
    )
