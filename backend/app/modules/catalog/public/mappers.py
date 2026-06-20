"""Public studio DTO → API response schemas."""

from app.modules.catalog.public import (
    PublicService,
    PublicServiceDTO,
    StudioPublicDTO,
    StudioPublicResponse,
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
        logo_url=dto.logo_url,
        cover_url=dto.cover_url,
        services=[_map_public_service(service) for service in dto.services],
    )
