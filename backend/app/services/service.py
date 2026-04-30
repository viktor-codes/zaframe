"""
Бизнес-логика для Service / Schedule и генерации occurrence'ов (Slot).

Здесь живут:
- генерация расписания на основе Schedule / параметров
- проверка доступности курса с учётом soft/hard лимитов (overbooking)
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from app.core.datetime_utils import to_naive_utc
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models import (
    Booking,
    BookingStatus,
    BookingType,
    Order,
    OrderStatus,
    Schedule,
    Service,
    ServiceType,
    Slot,
)
from app.schemas import (
    CourseAvailabilityResult,
    CourseBookingCreate,
    CourseBookingPreviewItem,
    CourseBookingResponse,
    OrderResponse,
    PublicService,
    ScheduleCreate,
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
    ServiceUpdate,
    StudioPublicResponse,
)


def _combine_date_time(d: date, t: time) -> datetime:
    """Комбинирует date + time и приводит к naive UTC."""
    dt = datetime.combine(d, t)
    return to_naive_utc(dt)


async def create_service(uow: UnitOfWork, studio_id: int, data: dict) -> Service:
    """Создать услугу."""
    service = Service(studio_id=studio_id, **data)
    uow.session.add(service)
    await uow.session.flush()
    await uow.session.refresh(service)
    return service


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
    await uow.session.flush()
    await uow.session.refresh(service)
    return service


async def deactivate_service(uow: UnitOfWork, service: Service) -> Service:
    """Деактивировать услугу (не удаляем, чтобы не ломать слоты/бронирования)."""
    service.is_active = False
    await uow.session.flush()
    await uow.session.refresh(service)
    return service


async def create_schedule(uow: UnitOfWork, schema: ScheduleCreate) -> Schedule:
    """Создать шаблон расписания для услуги."""
    if await uow.services.get_by_id(schema.service_id) is None:
        raise NotFoundError("Service not found")

    schedule = Schedule(
        service_id=schema.service_id,
        day_of_week=schema.day_of_week,
        start_time=schema.start_time,
        valid_from=schema.valid_from,
        valid_to=schema.valid_to,
    )
    uow.session.add(schedule)
    await uow.session.flush()
    await uow.session.refresh(schedule)
    return schedule


async def get_schedules_for_service(
    uow: UnitOfWork,
    *,
    service_id: int,
) -> list[Schedule]:
    """Получить все шаблоны расписания для услуги."""
    return await uow.schedules.list_by_service_id(service_id)


async def get_schedule(uow: UnitOfWork, schedule_id: int) -> Schedule | None:
    """Получить один шаблон расписания."""
    return await uow.schedules.get_by_id(schedule_id)


async def delete_schedule(uow: UnitOfWork, schedule: Schedule) -> None:
    """Удалить шаблон расписания."""
    await uow.session.delete(schedule)
    await uow.session.flush()


async def get_schedule_or_raise(uow: UnitOfWork, schedule_id: int) -> Schedule:
    """Получить шаблон расписания или выбросить NotFoundError."""
    schedule = await uow.schedules.get_by_id(schedule_id)
    if schedule is None:
        raise NotFoundError("Schedule not found")
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
) -> list[Slot]:
    """
    Генератор occurrence'ов (Slot) для курса.

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

    start_date = start_date or date.today()

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

            start_dt = _combine_date_time(day_date, start_time)
            end_dt = start_dt + duration
            planned_intervals.append((start_dt, end_dt))

    if not planned_intervals:
        raise ValidationError(
            "Could not generate any sessions for the given parameters",
        )

    min_start = min(s for s, _ in planned_intervals)
    max_end = max(e for _, e in planned_intervals)

    existing_slots = await uow.slots.list_overlapping(studio_id, service_id, min_start, max_end)

    if existing_slots:
        raise ValidationError(
            "Existing course sessions overlap this period. Remove old sessions or pick another range.",
        )

    created_slots: list[Slot] = []
    for start_dt, end_dt in planned_intervals:
        slot = Slot(
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
        uow.session.add(slot)
        created_slots.append(slot)

    await uow.session.flush()
    for slot in created_slots:
        await uow.session.refresh(slot)
    return created_slots


@dataclass
class _CapacityStats:
    slot: Slot
    confirmed_count: int
    pending_count: int

    @property
    def total(self) -> int:
        return self.confirmed_count + self.pending_count


async def _get_course_slots_with_capacity(
    uow: UnitOfWork,
    *,
    service: Service,
    for_update: bool = False,
    now: datetime | None = None,
) -> list[_CapacityStats]:
    """Получить все слоты курса и их текущую заполненность."""
    now_utc = now or datetime.now(UTC)
    slots = await uow.slots.list_by_service_active(service.id, for_update=for_update)
    if not slots:
        return []

    slot_ids = [s.id for s in slots]
    counts_map = await uow.bookings.get_confirmed_pending_counts_by_slot_ids(
        slot_ids,
        now=now_utc,
    )

    return [
        _CapacityStats(
            slot=slot,
            confirmed_count=counts_map.get(slot.id, (0, 0))[0],
            pending_count=counts_map.get(slot.id, (0, 0))[1],
        )
        for slot in slots
    ]


async def check_course_availability(
    uow: UnitOfWork,
    *,
    service_id: int,
    for_update: bool = False,
    now: datetime | None = None,
) -> CourseAvailabilityResult:
    """
    Проверка доступности курса с учётом overbooking‑логики.
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")

    now_utc = now or datetime.now(UTC)
    stats = await _get_course_slots_with_capacity(
        uow,
        service=service,
        for_update=for_update,
        now=now_utc,
    )
    if not stats:
        return CourseAvailabilityResult(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_slots=[],
            message="No sessions have been created for this course yet",
        )

    overbooked_items: list[CourseBookingPreviewItem] = []
    hard_block = False

    for s in stats:
        max_capacity = s.slot.max_capacity
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
                CourseBookingPreviewItem(
                    slot_id=s.slot.id,
                    start_time=s.slot.start_time,
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
        return CourseAvailabilityResult(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_slots=overbooked_items,
            message="Not enough seats in several course sessions. Contact the studio owner.",
        )

    requires_warning = len(overbooked_items) > 0
    message = None
    if requires_warning:
        message = "Some course sessions will be fuller, but booking is still allowed."

    return CourseAvailabilityResult(
        can_book=True,
        requires_warning=requires_warning,
        hard_block=False,
        overbooked_slots=overbooked_items,
        message=message,
    )


async def create_course_booking(
    uow: UnitOfWork,
    *,
    schema: CourseBookingCreate,
) -> CourseBookingResponse:
    """
    Создать заказ и набор бронирований для курса (гостевой сценарий).

    Важно: операция атомарна в рамках AsyncSession/транзакции.
    """
    now_utc = datetime.now(UTC)
    availability = await check_course_availability(
        uow,
        service_id=schema.service_id,
        for_update=True,
        now=now_utc,
    )
    if not availability.can_book:
        raise ValidationError(
            availability.message or "Not enough seats for the course",
        )

    service = await uow.services.get_by_id_with_slots(schema.service_id)
    if service is None:
        raise NotFoundError("Service not found")

    slots = sorted(service.slots, key=lambda s: s.start_time)
    if not slots:
        raise ValidationError(
            "No sessions have been created for this course yet",
        )

    total_amount_cents = service.price_course_cents or (service.price_single_cents * len(slots))

    # Распределяем стоимость курса по занятиям так, чтобы сумма unit_price_cents
    # строго совпадала с total_amount_cents (решаем "The Cent Problem").
    base_unit = total_amount_cents // len(slots)
    remainder = total_amount_cents % len(slots)
    prices = [base_unit + 1] * remainder + [base_unit] * (len(slots) - remainder)

    order = Order(
        studio_id=service.studio_id,
        service_id=service.id,
        user_id=None,
        guest_email=schema.guest_email,
        guest_name=schema.guest_name,
        total_amount_cents=total_amount_cents,
        currency="eur",
        status=OrderStatus.PENDING,
    )
    uow.session.add(order)
    await uow.session.flush()
    await uow.session.refresh(order)

    bookings: list[Booking] = []
    for idx, slot in enumerate(slots):
        unit_price = prices[idx]
        booking = Booking(
            slot_id=slot.id,
            user_id=None,
            guest_session_id=None,
            guest_name=schema.guest_name,
            guest_email=schema.guest_email,
            guest_phone=schema.guest_phone,
            status=BookingStatus.PENDING,
            booking_type=BookingType.COURSE,
            service_id=service.id,
            order_id=order.id,
            unit_price_cents=unit_price,
        )
        uow.session.add(booking)
        bookings.append(booking)

    await uow.session.flush()
    for b in bookings:
        await uow.session.refresh(b)

    order_schema = OrderResponse.model_validate(order)
    # Отложим полноценный маппинг BookingResponse, пока основной поток остаётся single-slot
    from app.schemas.booking import (  # локальный импорт, чтобы избежать циклов
        BookingResponse,
    )

    booking_schemas = [BookingResponse.model_validate(b) for b in bookings]

    return CourseBookingResponse(
        order=order_schema,
        bookings=booking_schemas,
        availability=availability,
    )


async def get_studio_public(
    uow: UnitOfWork,
    *,
    slug: str,
) -> StudioPublicResponse:
    """
    Публичное представление студии по slug.

    Возвращает:
    - основную информацию о студии
    - список услуг с ближайшими occurrence'ами.
    """
    studio = await uow.studios.get_by_slug_with_services_slots(slug)
    if studio is None:
        raise NotFoundError("Studio not found")

    services_public: list[PublicService] = []

    # Собираем все будущие слоты студии, чтобы одним запросом посчитать заполненность.
    now_utc = datetime.now(UTC)
    all_upcoming_slots: list[Slot] = []
    for service in studio.services:
        for slot in service.slots:
            if slot.start_time >= now_utc and slot.is_active and slot.status == "active":
                all_upcoming_slots.append(slot)

    slot_capacity_map: dict[int, tuple[int, int]] = {}
    if all_upcoming_slots:
        slot_ids = [s.id for s in all_upcoming_slots]
        slot_capacity_map = await uow.bookings.get_confirmed_pending_counts_by_slot_ids(
            slot_ids,
            now=now_utc,
        )

    for service in studio.services:
        # Берём только будущие слоты этого сервиса (уже загружены через selectinload)
        upcoming_slots = [
            s
            for s in service.slots
            if s.start_time >= now_utc and s.is_active and s.status == "active"
        ]
        upcoming_slots.sort(key=lambda s: s.start_time)

        if upcoming_slots:
            next_term_start = upcoming_slots[0].start_time
            term_end = upcoming_slots[-1].end_time
            occurrences_count = len(upcoming_slots)
        else:
            next_term_start = None
            term_end = None
            occurrences_count = 0

        availability_schema: PublicService.Availability | None = None
        if service.type == ServiceType.COURSE and upcoming_slots:
            total_remaining_capacity = 0
            overbooked_dates_set: set[date] = set()
            overbooked_slots_count = 0

            for slot in upcoming_slots:
                confirmed, pending = slot_capacity_map.get(slot.id, (0, 0))
                current_total = confirmed + pending
                remaining = max(0, slot.max_capacity - current_total)
                total_remaining_capacity += remaining

                status = service.get_capacity_status(
                    max_capacity=slot.max_capacity,
                    current_bookings=current_total,
                    requested=1,
                )
                is_over_soft = status == "SOFT_LIMIT_REACHED"
                is_over_hard = status == "HARD_LIMIT_REACHED"

                if is_over_soft or is_over_hard:
                    overbooked_slots_count += 1
                    overbooked_dates_set.add(slot.start_time.date())

            requires_warning = overbooked_slots_count > 0
            hard_block = False
            if occurrences_count > 0:
                overbooked_ratio = overbooked_slots_count / occurrences_count
                if overbooked_ratio > service.max_overbooked_ratio:
                    hard_block = True

            can_book = occurrences_count > 0 and total_remaining_capacity > 0 and not hard_block

            availability_schema = PublicService.Availability(
                can_book=can_book,
                total_remaining_capacity=total_remaining_capacity,
                requires_warning=requires_warning and not hard_block,
                overbooked_dates=sorted(overbooked_dates_set),
            )

        services_public.append(
            PublicService(
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
                availability=availability_schema,
            )
        )

    return StudioPublicResponse(
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
) -> ServiceAvailabilityResponse:
    """
    Детальная информация о доступности курса по всем его занятиям.

    Используется для pre‑check перед оплатой (модалка с календарём).
    """
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if service.type != ServiceType.COURSE:
        raise ValidationError("Service is not a course")

    now_utc = datetime.now(UTC)
    availability = await check_course_availability(
        uow,
        service_id=service_id,
        for_update=False,
        now=now_utc,
    )

    stats = await _get_course_slots_with_capacity(
        uow,
        service=service,
        now=now_utc,
    )
    if start_date is not None:
        stats = [s for s in stats if s.slot.start_time.date() >= start_date]

    details: list[ServiceAvailabilityScheduleItem] = []
    for s in stats:
        max_capacity = s.slot.max_capacity
        status = service.get_capacity_status(
            max_capacity=max_capacity,
            current_bookings=s.total,
            requested=1,
        )
        is_over_hard = status == "HARD_LIMIT_REACHED"
        is_over_soft = status == "SOFT_LIMIT_REACHED"

        remaining = max(0, max_capacity - s.total)

        details.append(
            ServiceAvailabilityScheduleItem(
                date=s.slot.start_time.date(),
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

    return ServiceAvailabilityResponse(
        service_id=service_id,
        can_book=availability.can_book,
        requires_warning=availability.requires_warning,
        warning_message=availability.message,
        schedule_details=details,
    )
