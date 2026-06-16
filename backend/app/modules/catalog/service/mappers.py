"""Service availability DTO → API response schemas."""

from app.modules.catalog.service import (
    ServiceAvailabilityDTO,
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
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
