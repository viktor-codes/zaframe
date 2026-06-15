"""
Бизнес-логика для Service / ScheduleTemplate и генерации occurrence'ов (Occurrence).

Здесь живут:
- генерация расписания на основе ScheduleTemplate / параметров
- проверка доступности курса с учётом soft/hard лимитов (overbooking)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import studio_local_date_now, studio_local_to_utc, utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models import (
    Booking,
    BookingStatus,
    BookingType,
    Order,
    OrderStatus,
    ScheduleTemplate,
    Service,
    ServiceType,
    Occurrence,
)
from app.schemas import ScheduleTemplateCreate, ServiceUpdate
from app.services.dto import (
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


async def create_schedule_template(
    uow: UnitOfWork, schema: ScheduleTemplateCreate
) -> ScheduleTemplate:
    """Создать шаблон расписания для услуги."""
    if await uow.services.get_by_id(schema.service_id) is None:
        raise NotFoundError("Service not found")

    schedule_template = ScheduleTemplate(
        service_id=schema.service_id,
        day_of_week=schema.day_of_week,
        start_time=schema.start_time,
        valid_from=schema.valid_from,
        valid_to=schema.valid_to,
    )
    return await uow.schedule_templates.add(schedule_template)


async def get_schedule_templates_for_service(
    uow: UnitOfWork,
    *,
    service_id: int,
) -> list[ScheduleTemplate]:
    """Получить все шаблоны расписания для услуги."""
    return await uow.schedule_templates.list_by_service_id(service_id)


async def get_schedule_template(uow: UnitOfWork, schedule_template_id: int) -> ScheduleTemplate | None:
    """Получить один шаблон расписания."""
    return await uow.schedule_templates.get_by_id(schedule_template_id)


async def delete_schedule_template(uow: UnitOfWork, schedule: ScheduleTemplate) -> None:
    """Удалить шаблон расписания."""
    await uow.schedule_templates.delete(schedule)


async def get_schedule_template_or_raise(
    uow: UnitOfWork, schedule_template_id: int
) -> ScheduleTemplate:
    """Получить шаблон расписания или выбросить NotFoundError."""
    schedule = await uow.schedule_templates.get_by_id(schedule_template_id)
    if schedule is None:
        raise NotFoundError("ScheduleTemplate not found")
    return schedule


def _iterate_weeks(start: date, weeks_count: int) -> Iterable[date]:
    """Генерирует даты начала недель (по понедельникам) для заданного количества недель."""
    current = start
    for _ in range(weeks_count):
        yield current
        current = current + timedelta(weeks=1)


async def occurrence_generator(
    uow: UnitOfWork,
    *,
    studio_id: int,
    service_id: int,
    days: list[int],
    start_time: time,
    weeks_count: int,
    start_date: date | None = None,
) -> list[Occurrence]:
    """
    Генератор occurrence'ов (Occurrence) для курса.

    Используется сценарием:
    POST /studios/{id}/generate-schedule
    Payload: {service_id, days: [1,3], start_time, weeks_count}
    """
    if weeks_count <= 0:
        raise ValidationError("weeks_count must be greater than 0")
    if not days:
        raise ValidationError("days list cannot be empty")

    service = await uow.services.get_by_studio_and_id(studio_id, service_id)
    if service is None:
        raise NotFoundError("Service not found in this studio")

    studio = await uow.studios.get_by_id(studio_id)
    if studio is None:
        raise NotFoundError("Studio not found")

    start_date = start_date or studio_local_date_now(studio.timezone)

    # Нормализуем start_date к ближайшему понедельнику назад, чтобы удобно идти по неделям.
    start_monday = start_date - timedelta(days=start_date.weekday())

    # Сначала считаем все планируемые интервалы, потом одним запросом ищем пересечения,
    # чтобы не плодить "мёртвые" слоты при повторной генерации.
    planned_intervals: list[tuple[datetime, datetime]] = []
    duration = timedelta(minutes=service.duration_minutes)

    for week_start in _iterate_weeks(start_monday, weeks_count):
        for dow in days:
            if not 0 <= dow <= 6:
                raise ValidationError("day_of_week must be between 0 and 6")
            day_date = week_start + timedelta(days=dow)
            if day_date < start_date:
                # Пропускаем занятия до стартовой даты
                continue

            start_dt = studio_local_to_utc(day_date, start_time, studio.timezone)
            end_dt = start_dt + duration
            planned_intervals.append((start_dt, end_dt))

    if not planned_intervals:
        raise ValidationError(
            "Could not generate any sessions for the given parameters",
        )

    min_start = min(s for s, _ in planned_intervals)
    max_end = max(e for _, e in planned_intervals)

    existing_occurrences = await uow.occurrences.list_overlapping(studio_id, service_id, min_start, max_end)

    if existing_occurrences:
        raise ValidationError(
            "Existing course sessions overlap this period. Remove old sessions or pick another range.",
        )

    created_occurrences: list[Occurrence] = []
    for start_dt, end_dt in planned_intervals:
        occurrence = Occurrence(
            studio_id=studio_id,
            service_id=service_id,
            start_time=start_dt,
            end_time=end_dt,
            title=service.name,
            description=service.description,
            max_capacity=service.max_capacity,
            price_cents=service.price_single_cents,
            course_price_cents=service.price_course_cents,
        )
        created_occurrences.append(occurrence)

    return await uow.occurrences.add_all(created_occurrences)


@dataclass
class _CapacityStats:
    occurrence: Occurrence
    confirmed_count: int
    pending_count: int

    @property
    def total(self) -> int:
        return self.confirmed_count + self.pending_count


async def _get_course_slots_with_capacity(
    uow: UnitOfWork,
    *,
    service: Service,
    now: datetime | None = None,
) -> list[_CapacityStats]:
    """Получить все слоты курса и их текущую заполненность."""
    now_utc = now or utc_now()
    occurrences = await uow.occurrences.list_by_service_active(service.id)
    return await _build_course_capacity_stats(uow, occurrences=occurrences, now=now_utc)


async def _get_course_slots_with_capacity_for_update(
    uow: UnitOfWork,
    *,
    service: Service,
    now: datetime | None = None,
) -> list[_CapacityStats]:
    """Lock active course occurrences, then read their fill levels for booking."""
    now_utc = now or utc_now()
    occurrences = await uow.occurrences.list_by_service_active_for_update(service.id)
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
            message="No sessions have been created for this course yet",
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
    stats = await _get_course_slots_with_capacity(
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
    stats = await _get_course_slots_with_capacity_for_update(
        uow,
        service=service,
        now=now_utc,
    )
    return _evaluate_course_availability(service, stats)


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

    service = await uow.services.get_by_id_with_occurrences(data.service_id)
    if service is None:
        raise NotFoundError("Service not found")

    occurrences = sorted(service.occurrences, key=lambda s: s.start_time)
    if not occurrences:
        raise ValidationError(
            "No sessions have been created for this course yet",
        )

    total_amount_cents = service.price_course_cents or (service.price_single_cents * len(occurrences))

    # Распределяем стоимость курса по занятиям так, чтобы сумма unit_price_cents
    # строго совпадала с total_amount_cents (решаем "The Cent Problem").
    base_unit = total_amount_cents // len(occurrences)
    remainder = total_amount_cents % len(occurrences)
    prices = [base_unit + 1] * remainder + [base_unit] * (len(occurrences) - remainder)

    order = await uow.orders.add(
        Order(
            studio_id=service.studio_id,
            service_id=service.id,
            user_id=None,
            guest_email=data.guest_email,
            guest_name=data.guest_name,
            total_amount_cents=total_amount_cents,
            currency="eur",
            status=OrderStatus.PENDING,
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
    studio = await uow.studios.get_by_slug_with_services_slots(slug)
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

    stats = await _get_course_slots_with_capacity(
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
