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
    Публичное представление студии по slug.

    Возвращает:
    - основную информацию о студии
    - список услуг с ближайшими occurrence'ами.
    """
    studio = await uow.studios.get_by_slug_with_services_occurrences(slug)
    if studio is None:
        raise NotFoundError("Studio not found")

    services_public: list[PublicServiceDTO] = []

    # Собираем все будущие слоты студии, чтобы одним запросом посчитать заполненность.
    now_utc = utc_now()
    all_upcoming_occurrences: list[Occurrence] = []
    for service in studio.services:
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
                cover_image_url=None,  # можно будет добавить из отдельного поля/таблицы
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
        services=services_public,
    )
