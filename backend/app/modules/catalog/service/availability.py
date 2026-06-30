"""Public course availability service functions."""

from __future__ import annotations

from datetime import date, datetime
from typing import cast

from app.core import datetime_utils
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models import ServiceType
from app.modules.catalog.capacity import (
    CapacityServiceLike,
    classify_occurrence_capacity,
    is_occurrence_overbooked,
    overbooking_status_label,
)
from app.modules.catalog.service.availability_stats import (
    evaluate_course_availability,
    get_course_occurrences_with_capacity,
    get_course_occurrences_with_capacity_for_update,
)
from app.modules.catalog.service.dto import (
    CourseAvailabilityDTO,
    ServiceAvailabilityDTO,
    ServiceAvailabilityScheduleItemDTO,
)


async def check_course_availability(
    uow: UnitOfWork,
    *,
    service_id: int,
    now: datetime | None = None,
) -> CourseAvailabilityDTO:
    """Check course availability with overbooking rules."""
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")
    if not service.is_bookable():
        raise ValidationError("Service is not available for booking")

    now_utc = now or datetime_utils.utc_now()
    stats = await get_course_occurrences_with_capacity(
        uow,
        service=service,
        now=now_utc,
    )
    return evaluate_course_availability(service, stats)


async def check_course_availability_for_update(
    uow: UnitOfWork,
    *,
    service_id: int,
    now: datetime | None = None,
) -> CourseAvailabilityDTO:
    """
    Check course availability with row locks (FOR UPDATE).

    Used before creating a booking to avoid capacity races.
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")
    if not service.is_bookable():
        raise ValidationError("Service is not available for booking")

    now_utc = now or datetime_utils.utc_now()
    stats = await get_course_occurrences_with_capacity_for_update(
        uow,
        service=service,
        now=now_utc,
    )
    return evaluate_course_availability(service, stats)


async def get_service_availability(
    uow: UnitOfWork,
    *,
    service_id: int,
    start_date: date | None = None,
) -> ServiceAvailabilityDTO:
    """
    Detailed course availability across all upcoming sessions.

    Used for pre-payment checks (calendar modal).
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")

    now_utc = datetime_utils.utc_now()
    stats = await get_course_occurrences_with_capacity(
        uow,
        service=service,
        now=now_utc,
    )
    availability = evaluate_course_availability(service, stats)
    if start_date is not None:
        stats = [s for s in stats if s.occurrence.start_time.date() >= start_date]

    details: list[ServiceAvailabilityScheduleItemDTO] = []
    for s in stats:
        flags = classify_occurrence_capacity(
            cast(CapacityServiceLike, service),
            max_capacity=s.occurrence.max_capacity,
            current_bookings=s.total,
        )
        details.append(
            ServiceAvailabilityScheduleItemDTO(
                date=s.occurrence.start_time.date(),
                is_overbooked=is_occurrence_overbooked(flags),
                remaining=flags.remaining,
                overbooking_status=overbooking_status_label(flags),
            )
        )

    return ServiceAvailabilityDTO(
        service_id=service_id,
        can_book=availability.can_book,
        requires_warning=availability.requires_warning,
        warning_message=availability.message,
        schedule_details=details,
    )
