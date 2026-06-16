"""
Бизнес-логика для Service: CRUD и проверка доступности курса (overbooking).

Здесь живут:
- CRUD услуг (Service)
- проверка доступности курса с учётом soft/hard лимитов (overbooking)

Временные «жильцы» (переезжают в следующих шагах рефакторинга):
- get_studio_public → catalog/public (tz-08)
- create_course_booking → booking/order (tz-09)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.access_tokens import generate_resource_access_token
from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models import (
    Booking,
    BookingStatus,
    BookingType,
    Occurrence,
    Order,
    OrderStatus,
    Service,
    ServiceType,
)
from app.modules.catalog.service.dto import (
    CourseAvailabilityDTO,
    CourseBookingInput,
    CourseBookingPreviewItemDTO,
    CourseBookingResultDTO,
    PublicServiceAvailabilityDTO,
    PublicServiceDTO,
    ServiceAvailabilityDTO,
    ServiceAvailabilityScheduleItemDTO,
    StudioPublicDTO,
)
from app.modules.catalog.service.schemas import ServiceUpdate

# WHY: temporary tenant create_course_booking still calls in-domain booking helpers
# via the legacy facade; resolved when it relocates to booking/order in tz-09.
from app.services.booking import _ensure_no_active_booking_for_guest, _persist_bookings


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


def _calculate_course_order_total_cents(
    service: Service,
    *,
    bookable_occurrence_count: int,
    total_active_occurrence_count: int,
) -> int:
    """
    Course order total for the bookable (active, future) occurrence set.

    When price_course_cents is set, charge proportionally to remaining sessions
    vs all active sessions on the course (mid-term joiners pay a fair share).
    """
    if bookable_occurrence_count <= 0:
        raise ValidationError("Course has no upcoming sessions")

    if service.price_course_cents is not None:
        denominator = total_active_occurrence_count or bookable_occurrence_count
        return round(
            service.price_course_cents * bookable_occurrence_count / denominator,
        )

    return service.price_single_cents * bookable_occurrence_count


def _distribute_course_unit_prices(
    total_amount_cents: int,
    occurrence_count: int,
) -> list[int]:
    """Split order total across occurrences; sum(unit_price_cents) == total_amount_cents."""
    base_unit = total_amount_cents // occurrence_count
    remainder = total_amount_cents % occurrence_count
    return [base_unit + 1] * remainder + [base_unit] * (occurrence_count - remainder)


async def create_course_booking(
    uow: UnitOfWork,
    *,
    data: CourseBookingInput,
) -> CourseBookingResultDTO:
    """
    Создать заказ и набор бронирований для курса (гостевой сценарий).

    Важно: операция атомарна в рамках AsyncSession/транзакции.
    """
    now_utc = utc_now()
    availability = await check_course_availability_for_update(
        uow,
        service_id=data.service_id,
        now=now_utc,
    )
    if not availability.can_book:
        raise ValidationError(
            availability.message or "Not enough seats for the course",
        )

    service = await uow.services.get_by_id(data.service_id)
    if service is None:
        raise NotFoundError("Service not found")

    occurrences = await uow.occurrences.list_active_future_by_service_for_update(
        data.service_id,
        now=now_utc,
    )
    occurrences = sorted(occurrences, key=lambda o: o.start_time)
    if not occurrences:
        raise ValidationError("Course has no upcoming sessions")

    all_active_occurrences = await uow.occurrences.list_by_service_active(service.id)
    total_amount_cents = _calculate_course_order_total_cents(
        service,
        bookable_occurrence_count=len(occurrences),
        total_active_occurrence_count=len(all_active_occurrences),
    )
    prices = _distribute_course_unit_prices(total_amount_cents, len(occurrences))

    order = await uow.orders.add(
        Order(
            studio_id=service.studio_id,
            service_id=service.id,
            user_id=None,
            guest_email=data.guest_email,
            guest_name=data.guest_name,
            guest_phone=data.guest_phone,
            total_amount_cents=total_amount_cents,
            currency="eur",
            status=OrderStatus.PENDING,
            access_token=generate_resource_access_token(),
        )
    )

    bookings: list[Booking] = []
    for idx, occurrence in enumerate(occurrences):
        await _ensure_no_active_booking_for_guest(
            uow,
            occurrence_id=occurrence.id,
            guest_email=data.guest_email,
        )
        unit_price = prices[idx]
        bookings.append(
            Booking(
                occurrence_id=occurrence.id,
                user_id=None,
                guest_name=data.guest_name,
                guest_email=data.guest_email,
                guest_phone=data.guest_phone,
                status=BookingStatus.PENDING,
                reserved_until=get_booking_reserved_until(now=now_utc),
                booking_type=BookingType.COURSE,
                service_id=service.id,
                order_id=order.id,
                unit_price_cents=unit_price,
            )
        )

    bookings = await _persist_bookings(uow, bookings)

    return CourseBookingResultDTO(
        order=order,
        bookings=bookings,
        availability=availability,
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
            o
            for o in service.occurrences
            if o.start_time >= now_utc and o.is_bookable()
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
            total_remaining_capacity = 0
            overbooked_dates_set: set[date] = set()
            overbooked_occurrences_count = 0

            for occurrence in upcoming_occurrences:
                confirmed, pending = occurrence_capacity_map.get(occurrence.id, (0, 0))
                current_total = confirmed + pending
                remaining = max(0, occurrence.max_capacity - current_total)
                total_remaining_capacity += remaining

                status = service.get_capacity_status(
                    max_capacity=occurrence.max_capacity,
                    current_bookings=current_total,
                    requested=1,
                )
                is_over_soft = status == "SOFT_LIMIT_REACHED"
                is_over_hard = status == "HARD_LIMIT_REACHED"

                if is_over_soft or is_over_hard:
                    overbooked_occurrences_count += 1
                    overbooked_dates_set.add(occurrence.start_time.date())

            requires_warning = overbooked_occurrences_count > 0
            hard_block = False
            if occurrences_count > 0:
                overbooked_ratio = overbooked_occurrences_count / occurrences_count
                if overbooked_ratio > service.max_overbooked_ratio:
                    hard_block = True

            can_book = occurrences_count > 0 and total_remaining_capacity > 0 and not hard_block

            availability_dto = PublicServiceAvailabilityDTO(
                can_book=can_book,
                total_remaining_capacity=total_remaining_capacity,
                requires_warning=requires_warning and not hard_block,
                overbooked_dates=sorted(overbooked_dates_set),
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
