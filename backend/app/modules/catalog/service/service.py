"""
Бизнес-логика для Service: CRUD и проверка доступности курса (overbooking).

Здесь живут:
- CRUD услуг (Service)
- проверка доступности курса с учётом soft/hard лимитов (overbooking)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.datetime_utils import utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models import Occurrence, Service, ServiceType
from app.modules.catalog.service.dto import (
    CourseAvailabilityDTO,
    CourseBookingPreviewItemDTO,
    ServiceAvailabilityDTO,
    ServiceAvailabilityScheduleItemDTO,
)
from app.modules.catalog.service.schemas import ServiceUpdate


async def create_service(uow: UnitOfWork, studio_id: int, data: dict) -> Service:
    """Создать услугу."""
    service = Service(studio_id=studio_id, **data)
    return await uow.services.add(service)


async def get_service(uow: UnitOfWork, service_id: int) -> Service | None:
    """Получить услугу по ID."""
    return await uow.services.get_by_id(service_id)


async def get_service_or_raise(uow: UnitOfWork, service_id: int) -> Service:
    """Получить услугу по ID или выбросить NotFoundError."""
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    return service


async def update_service(
    uow: UnitOfWork,
    service: Service,
    schema: ServiceUpdate,
) -> Service:
    """Обновить услугу (partial update)."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    return await uow.services.save(service)


async def deactivate_service(uow: UnitOfWork, service: Service) -> Service:
    """Деактивировать услугу (не удаляем, чтобы не ломать слоты/бронирования)."""
    service.is_active = False
    return await uow.services.save(service)


@dataclass
class _CapacityStats:
    occurrence: Occurrence
    confirmed_count: int
    pending_count: int

    @property
    def total(self) -> int:
        return self.confirmed_count + self.pending_count


async def _get_course_occurrences_with_capacity(
    uow: UnitOfWork,
    *,
    service: Service,
    now: datetime | None = None,
) -> list[_CapacityStats]:
    """Load active future course occurrences and their fill levels."""
    now_utc = now or utc_now()
    occurrences = await uow.occurrences.list_active_future_by_service(
        service.id,
        now=now_utc,
    )
    return await _build_course_capacity_stats(uow, occurrences=occurrences, now=now_utc)


async def _get_course_occurrences_with_capacity_for_update(
    uow: UnitOfWork,
    *,
    service: Service,
    now: datetime | None = None,
) -> list[_CapacityStats]:
    """Lock active future course occurrences, then read fill levels for booking."""
    now_utc = now or utc_now()
    occurrences = await uow.occurrences.list_active_future_by_service_for_update(
        service.id,
        now=now_utc,
    )
    occurrences = sorted(occurrences, key=lambda o: o.start_time)
    return await _build_course_capacity_stats(uow, occurrences=occurrences, now=now_utc)


async def _build_course_capacity_stats(
    uow: UnitOfWork,
    *,
    occurrences: list[Occurrence],
    now: datetime,
) -> list[_CapacityStats]:
    if not occurrences:
        return []

    occurrence_ids = [o.id for o in occurrences]
    counts_map = await uow.bookings.get_confirmed_pending_counts_by_occurrence_ids(
        occurrence_ids,
        now=now,
    )

    return [
        _CapacityStats(
            occurrence=occurrence,
            confirmed_count=counts_map.get(occurrence.id, (0, 0))[0],
            pending_count=counts_map.get(occurrence.id, (0, 0))[1],
        )
        for occurrence in occurrences
    ]


def _evaluate_course_availability(
    service: Service,
    stats: list[_CapacityStats],
) -> CourseAvailabilityDTO:
    if not stats:
        return CourseAvailabilityDTO(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_occurrences=[],
            message="Course has no upcoming sessions",
        )

    overbooked_items: list[CourseBookingPreviewItemDTO] = []
    hard_block = False

    for s in stats:
        max_capacity = s.occurrence.max_capacity
        status = service.get_capacity_status(
            max_capacity=max_capacity,
            current_bookings=s.total,
            requested=1,
        )
        is_over_hard = status == "HARD_LIMIT_REACHED"
        is_over_soft = status == "SOFT_LIMIT_REACHED"
        total_after = s.total + 1  # учитываем текущего потенциального покупателя

        if is_over_hard:
            hard_block = True

        if is_over_soft or is_over_hard:
            overbooked_items.append(
                CourseBookingPreviewItemDTO(
                    occurrence_id=s.occurrence.id,
                    start_time=s.occurrence.start_time,
                    max_capacity=max_capacity,
                    confirmed_count=s.confirmed_count,
                    pending_count=s.pending_count,
                    total_after_booking=total_after,
                    is_over_soft_limit=is_over_soft,
                    is_over_hard_limit=is_over_hard,
                )
            )

    # Доля слотов, где произойдёт overbooking
    overbooked_ratio = len(overbooked_items) / len(stats)

    if hard_block or overbooked_ratio > service.max_overbooked_ratio:
        return CourseAvailabilityDTO(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_occurrences=overbooked_items,
            message="Not enough seats in several course sessions. Contact the studio owner.",
        )

    requires_warning = len(overbooked_items) > 0
    message = None
    if requires_warning:
        message = "Some course sessions will be fuller, but booking is still allowed."

    return CourseAvailabilityDTO(
        can_book=True,
        requires_warning=requires_warning,
        hard_block=False,
        overbooked_occurrences=overbooked_items,
        message=message,
    )


async def check_course_availability(
    uow: UnitOfWork,
    *,
    service_id: int,
    now: datetime | None = None,
) -> CourseAvailabilityDTO:
    """
    Проверка доступности курса с учётом overbooking‑логики.
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")

    now_utc = now or utc_now()
    stats = await _get_course_occurrences_with_capacity(
        uow,
        service=service,
        now=now_utc,
    )
    return _evaluate_course_availability(service, stats)


async def check_course_availability_for_update(
    uow: UnitOfWork,
    *,
    service_id: int,
    now: datetime | None = None,
) -> CourseAvailabilityDTO:
    """
    Проверка доступности курса с блокировкой слотов (FOR UPDATE).

    Используется перед созданием бронирования, чтобы исключить гонки по местам.
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")

    now_utc = now or utc_now()
    stats = await _get_course_occurrences_with_capacity_for_update(
        uow,
        service=service,
        now=now_utc,
    )
    return _evaluate_course_availability(service, stats)


async def get_service_availability(
    uow: UnitOfWork,
    *,
    service_id: int,
    start_date: date | None = None,
) -> ServiceAvailabilityDTO:
    """
    Детальная информация о доступности курса по всем его занятиям.

    Используется для pre‑check перед оплатой (модалка с календарём).
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")

    now_utc = utc_now()
    availability = await check_course_availability(
        uow,
        service_id=service_id,
        now=now_utc,
    )

    stats = await _get_course_occurrences_with_capacity(
        uow,
        service=service,
        now=now_utc,
    )
    if start_date is not None:
        stats = [s for s in stats if s.occurrence.start_time.date() >= start_date]

    details: list[ServiceAvailabilityScheduleItemDTO] = []
    for s in stats:
        max_capacity = s.occurrence.max_capacity
        status = service.get_capacity_status(
            max_capacity=max_capacity,
            current_bookings=s.total,
            requested=1,
        )
        is_over_hard = status == "HARD_LIMIT_REACHED"
        is_over_soft = status == "SOFT_LIMIT_REACHED"

        remaining = max(0, max_capacity - s.total)

        details.append(
            ServiceAvailabilityScheduleItemDTO(
                date=s.occurrence.start_time.date(),
                is_overbooked=is_over_soft or is_over_hard,
                remaining=remaining,
                overbooking_status=(
                    "HARD_LIMIT_REACHED"
                    if is_over_hard
                    else "SOFT_LIMIT_REACHED"
                    if is_over_soft
                    else None
                ),
            )
        )

    return ServiceAvailabilityDTO(
        service_id=service_id,
        can_book=availability.can_book,
        requires_warning=availability.requires_warning,
        warning_message=availability.message,
        schedule_details=details,
    )
