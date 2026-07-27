"""Public storefront aggregate: studio profile + service catalog for anonymous users."""

from __future__ import annotations

from datetime import date
from typing import cast

from app.core.datetime_utils import utc_now
from app.core.exceptions import NotFoundError
from app.core.uow import UnitOfWork
from app.models import Occurrence, ServiceType
from app.modules.catalog.capacity import (
    CapacityServiceLike,
    OccurrenceFill,
    build_public_course_availability,
)
from app.modules.catalog.occurrence.schemas import OccurrenceResponse
from app.modules.catalog.public.dto import (
    PublicServiceAvailabilityDTO,
    PublicServiceDTO,
    StudioPublicDTO,
)


async def get_studio_public(
    uow: UnitOfWork,
    *,
    slug: str,
) -> StudioPublicDTO:
    """
    Public studio representation by slug.

    Returns:
    - core studio information
    - services with upcoming occurrences.
    """
    studio = await uow.studios.get_by_slug_with_services_occurrences(slug)
    if studio is None:
        raise NotFoundError("Studio not found")

    services_public: list[PublicServiceDTO] = []

    # Collect all upcoming studio occurrences to calculate fill counts in one query.
    now_utc = utc_now()
    all_upcoming_occurrences: list[Occurrence] = []
    for service in studio.services:
        if not service.is_publicly_visible():
            continue
        for occurrence in service.occurrences:
            if occurrence.start_time >= now_utc and occurrence.is_bookable():
                all_upcoming_occurrences.append(occurrence)

    occurrence_capacity_map: dict[int, tuple[int, int]] = {}
    if all_upcoming_occurrences:
        occurrence_ids = [o.id for o in all_upcoming_occurrences]
        occurrence_capacity_map = await uow.bookings.get_confirmed_pending_counts_by_occurrence_ids(
            occurrence_ids,
            now=now_utc,
        )

    for service in studio.services:
        if not service.is_publicly_visible():
            continue
        upcoming_occurrences = [
            o for o in service.occurrences if o.start_time >= now_utc and o.is_bookable()
        ]
        upcoming_occurrences.sort(key=lambda o: o.start_time)

        if upcoming_occurrences:
            next_term_start = upcoming_occurrences[0].start_time
            term_end = upcoming_occurrences[-1].end_time
            occurrences_count = len(upcoming_occurrences)
        else:
            next_term_start = None
            term_end = None
            occurrences_count = 0

        availability_dto: PublicServiceAvailabilityDTO | None = None
        if service.type == ServiceType.COURSE and upcoming_occurrences:
            fills: list[OccurrenceFill] = []
            occurrence_dates: list[date] = []
            for occurrence in upcoming_occurrences:
                confirmed, pending = occurrence_capacity_map.get(occurrence.id, (0, 0))
                fills.append(
                    OccurrenceFill(
                        occurrence_id=occurrence.id,
                        max_capacity=occurrence.max_capacity,
                        confirmed_count=confirmed,
                        pending_count=pending,
                    )
                )
                occurrence_dates.append(occurrence.start_time.date())

            availability_dto = build_public_course_availability(
                cast(CapacityServiceLike, service),
                fills,
                occurrence_dates=occurrence_dates,
            )

        services_public.append(
            PublicServiceDTO(
                id=service.id,
                name=service.name,
                description=service.description,
                type=service.type,
                duration_minutes=service.duration_minutes,
                max_capacity=service.max_capacity,
                price_single_cents=service.price_single_cents,
                price_course_cents=service.price_course_cents,
                cover_image_url=None,  # can be added later from a dedicated field/table
                next_term_start=next_term_start,
                term_end=term_end,
                occurrences_count=occurrences_count,
                availability=availability_dto,
            )
        )

    return StudioPublicDTO(
        id=studio.id,
        name=studio.name,
        slug=studio.slug,
        description=studio.description,
        logo_url=studio.logo_url,
        cover_url=studio.cover_url,
        services=services_public,
    )


async def list_public_bookable_occurrences(
    uow: UnitOfWork,
    *,
    slug: str,
    service_id: int,
) -> list[OccurrenceResponse]:
    """
    Upcoming scheduled occurrences for a public service, with seat counts.

    Used by the anonymous booking wizard (auth is not required).
    """
    studio = await uow.studios.get_by_slug(slug)
    if studio is None:
        raise NotFoundError("Studio not found")

    service = await uow.services.get_by_studio_and_id(studio.id, service_id)
    if service is None or not service.is_publicly_visible():
        raise NotFoundError("Service not found")

    now_utc = utc_now()
    occurrences = await uow.occurrences.list_active_future_by_service(
        service_id,
        now=now_utc,
    )
    if not occurrences:
        return []

    counts_map = await uow.bookings.get_confirmed_pending_counts_by_occurrence_ids(
        [occurrence.id for occurrence in occurrences],
        now=now_utc,
    )

    responses: list[OccurrenceResponse] = []
    for occurrence in occurrences:
        confirmed, pending = counts_map.get(occurrence.id, (0, 0))
        responses.append(
            OccurrenceResponse.model_validate(occurrence).model_copy(
                update={
                    "confirmed_count": confirmed,
                    "pending_count": pending,
                }
            )
        )
    return responses
