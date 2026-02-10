"""
Бизнес-логика для Service / Schedule и генерации occurrence'ов (Slot).

Здесь живут:
- генерация расписания на основе Schedule / параметров
- проверка доступности курса с учётом soft/hard лимитов (overbooking)
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, select, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    StudioPublicResponse,
    ServiceUpdate,
    ServiceResponse,
    ScheduleResponse,
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
)


def _to_naive_utc(dt: datetime) -> datetime:
    """Приводит datetime к naive UTC (как в core.database)."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _combine_date_time(d: date, t: time) -> datetime:
    """Комбинирует date + time и приводит к naive UTC."""
    dt = datetime.combine(d, t)
    return _to_naive_utc(dt)


async def create_service(db: AsyncSession, studio_id: int, data: dict) -> Service:
    """Создать услугу."""
    service = Service(
        studio_id=studio_id,
        **data,
    )
    db.add(service)
    await db.flush()
    await db.refresh(service)
    return service


async def get_service(db: AsyncSession, service_id: int) -> Service | None:
    """Получить услугу по ID."""
    result = await db.execute(select(Service).where(Service.id == service_id))
    return result.scalar_one_or_none()


async def update_service(
    db: AsyncSession,
    service: Service,
    schema: ServiceUpdate,
) -> Service:
    """Обновить услугу (partial update)."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    await db.flush()
    await db.refresh(service)
    return service


async def deactivate_service(db: AsyncSession, service: Service) -> Service:
    """
    Деактивировать услугу.

    Жёстко не удаляем, чтобы не ломать существующие слоты/бронирования.
    """
    service.is_active = False
    await db.flush()
    await db.refresh(service)
    return service


async def create_schedule(db: AsyncSession, schema: ScheduleCreate) -> Schedule:
    """Создать шаблон расписания для услуги."""
    # Проверяем, что услуга существует и принадлежит студии
    result = await db.execute(select(Service).where(Service.id == schema.service_id))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    schedule = Schedule(
        service_id=schema.service_id,
        day_of_week=schema.day_of_week,
        start_time=schema.start_time,
        valid_from=schema.valid_from,
        valid_to=schema.valid_to,
    )
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    return schedule


async def get_schedules_for_service(
    db: AsyncSession,
    *,
    service_id: int,
) -> list[Schedule]:
    """Получить все шаблоны расписания для услуги."""
    result = await db.execute(
        select(Schedule).where(Schedule.service_id == service_id).order_by(
            Schedule.day_of_week, Schedule.start_time
        )
    )
    return list(result.scalars().all())


async def get_schedule(db: AsyncSession, schedule_id: int) -> Schedule | None:
    """Получить один шаблон расписания."""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    return result.scalar_one_or_none()


async def delete_schedule(db: AsyncSession, schedule: Schedule) -> None:
    """Удалить шаблон расписания."""
    await db.delete(schedule)
    await db.flush()


def _iterate_weeks(start: date, weeks_count: int) -> Iterable[date]:
    """Генерирует даты начала недель (по понедельникам) для заданного количества недель."""
    current = start
    for _ in range(weeks_count):
        yield current
        current = current + timedelta(weeks=1)


async def occurrence_generator(
    db: AsyncSession,
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
        raise HTTPException(status_code=400, detail="weeks_count должен быть > 0")
    if not days:
        raise HTTPException(status_code=400, detail="Список days не может быть пустым")

    result = await db.execute(
        select(Service).where(
            Service.id == service_id,
            Service.studio_id == studio_id,
        )
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена в этой студии")

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
                raise HTTPException(
                    status_code=400,
                    detail="day_of_week должен быть в диапазоне 0-6",
                )
            day_date = week_start + timedelta(days=dow)
            if day_date < start_date:
                # Пропускаем занятия до стартовой даты
                continue

            start_dt = _combine_date_time(day_date, start_time)
            end_dt = start_dt + duration
            planned_intervals.append((start_dt, end_dt))

    if not planned_intervals:
        raise HTTPException(
            status_code=400,
            detail="Не удалось сгенерировать ни одного занятия для заданных параметров",
        )

    min_start = min(s for s, _ in planned_intervals)
    max_end = max(e for _, e in planned_intervals)

    # Проверка на наложение с уже существующими занятиями этого же сервиса.
    existing_q = (
        select(Slot)
        .where(
            Slot.studio_id == studio_id,
            Slot.service_id == service_id,
            Slot.start_time < max_end,
            Slot.end_time > min_start,
        )
    )
    existing_result = await db.execute(existing_q)
    existing_slots: list[Slot] = list(existing_result.scalars().all())

    if existing_slots:
        raise HTTPException(
            status_code=400,
            detail=(
                "Найдены уже существующие занятия этого курса в указанный период. "
                "Сначала удалите старые занятия или выберите другой интервал."
            ),
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
        db.add(slot)
        created_slots.append(slot)

    await db.flush()
    # Обновляем объекты, чтобы у них появились id
    for slot in created_slots:
        await db.refresh(slot)
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
    db: AsyncSession,
    *,
    service: Service,
    for_update: bool = False,
) -> list[_CapacityStats]:
    """Получить все слоты курса и их текущую заполненность."""
    slots_q = select(Slot).where(
        Slot.service_id == service.id,
        Slot.status == "active",
        Slot.is_active.is_(True),
    )
    if for_update:
        slots_q = slots_q.with_for_update()
    slots_q = slots_q.order_by(Slot.start_time.asc())
    slots_result = await db.execute(slots_q)
    slots: list[Slot] = list(slots_result.scalars().all())

    if not slots:
        return []

    slot_ids = [s.id for s in slots]
    # Считаем confirmed/pending по каждому слоту
    counts_q = select(
        Booking.slot_id,
        func.sum(
            case(
                (Booking.status == BookingStatus.CONFIRMED, 1),
                else_=0,
            )
        ).label("confirmed"),
        func.sum(
            case(
                (Booking.status == BookingStatus.PENDING, 1),
                else_=0,
            )
        ).label("pending"),
    ).where(Booking.slot_id.in_(slot_ids)).group_by(Booking.slot_id)
    counts_result = await db.execute(counts_q)
    counts_map: dict[int, tuple[int, int]] = {
        row.slot_id: (row.confirmed or 0, row.pending or 0)
        for row in counts_result
    }

    stats: list[_CapacityStats] = []
    for slot in slots:
        confirmed, pending = counts_map.get(slot.id, (0, 0))
        stats.append(
            _CapacityStats(
                slot=slot,
                confirmed_count=confirmed,
                pending_count=pending,
            )
        )
    return stats


async def check_course_availability(
    db: AsyncSession,
    *,
    service_id: int,
    for_update: bool = False,
) -> CourseAvailabilityResult:
    """
    Проверка доступности курса с учётом overbooking‑логики.

    Параметры:
    - soft_limit_ratio: до какого уровня относительно max_capacity считаем "нормой"
    - hard_limit_ratio: жёсткий предел (выше — блокируем покупку)
    - max_overbooked_ratio: доля слотов, которые могут быть сверх soft‑лимита
    """
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    if service.type != ServiceType.COURSE:
        raise HTTPException(status_code=400, detail="Услуга не является курсом")

    stats = await _get_course_slots_with_capacity(
        db,
        service=service,
        for_update=for_update,
    )
    if not stats:
        return CourseAvailabilityResult(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_slots=[],
            message="Для этого курса ещё не создано ни одного занятия",
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
            message="Недостаточно мест в нескольких занятиях курса. Свяжитесь с владельцем студии.",
        )

    requires_warning = len(overbooked_items) > 0
    message = None
    if requires_warning:
        message = "Некоторые занятия курса будут более плотными по количеству участников, но бронирование возможно."

    return CourseAvailabilityResult(
        can_book=True,
        requires_warning=requires_warning,
        hard_block=False,
        overbooked_slots=overbooked_items,
        message=message,
    )


async def create_course_booking(
    db: AsyncSession,
    *,
    schema: CourseBookingCreate,
) -> CourseBookingResponse:
    """
    Создать заказ и набор бронирований для курса (гостевой сценарий).

    Важно: операция атомарна в рамках AsyncSession/транзакции.
    """
    availability = await check_course_availability(
        db,
        service_id=schema.service_id,
        for_update=True,
    )
    if not availability.can_book:
        raise HTTPException(
            status_code=400,
            detail=availability.message or "Недостаточно мест для курса",
        )

    # Получаем слоты ещё раз, чтобы зафиксировать актуальный список
    result = await db.execute(
        select(Service)
        .options(selectinload(Service.slots))
        .where(Service.id == schema.service_id)
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")

    slots = sorted(service.slots, key=lambda s: s.start_time)
    if not slots:
        raise HTTPException(
            status_code=400,
            detail="Для этого курса ещё не создано ни одного занятия",
        )

    total_amount_cents = service.price_course_cents or (
        service.price_single_cents * len(slots)
    )

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
    db.add(order)
    await db.flush()
    await db.refresh(order)

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
        db.add(booking)
        bookings.append(booking)

    await db.flush()
    for b in bookings:
        await db.refresh(b)

    order_schema = OrderResponse.model_validate(order)
    # Отложим полноценный маппинг BookingResponse, пока основной поток остаётся single-slot
    from app.schemas.booking import BookingResponse  # локальный импорт, чтобы избежать циклов

    booking_schemas = [BookingResponse.model_validate(b) for b in bookings]

    return CourseBookingResponse(
        order=order_schema,
        bookings=booking_schemas,
        availability=availability,
    )


async def get_studio_public(
    db: AsyncSession,
    *,
    slug: str,
) -> StudioPublicResponse:
    """
    Публичное представление студии по slug.

    Возвращает:
    - основную информацию о студии
    - список услуг с ближайшими occurrence'ами.
    """
    from app.models import Studio  # локальный импорт, чтобы не плодить зависимостей

    studio_result = await db.execute(
        select(Studio)
        .options(selectinload(Studio.services).selectinload(Service.slots))
        .where(Studio.slug == slug, Studio.is_active.is_(True))
    )
    studio = studio_result.scalar_one_or_none()
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")

    services_public: list[PublicService] = []

    # Собираем все будущие слоты студии, чтобы одним запросом посчитать заполненность.
    now_utc = datetime.utcnow()
    all_upcoming_slots: list[Slot] = []
    for service in studio.services:
        for slot in service.slots:
            if (
                slot.start_time >= now_utc
                and slot.is_active
                and slot.status == "active"
            ):
                all_upcoming_slots.append(slot)

    slot_capacity_map: dict[int, tuple[int, int]] = {}
    if all_upcoming_slots:
        slot_ids = [s.id for s in all_upcoming_slots]
        counts_q = (
            select(
                Booking.slot_id,
                func.sum(
                    case(
                        (Booking.status == BookingStatus.CONFIRMED, 1),
                        else_=0,
                    )
                ).label("confirmed"),
                func.sum(
                    case(
                        (Booking.status == BookingStatus.PENDING, 1),
                        else_=0,
                    )
                ).label("pending"),
            )
            .where(Booking.slot_id.in_(slot_ids))
            .group_by(Booking.slot_id)
        )
        counts_result = await db.execute(counts_q)
        slot_capacity_map = {
            row.slot_id: (row.confirmed or 0, row.pending or 0)
            for row in counts_result
        }

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

            can_book = (
                occurrences_count > 0
                and total_remaining_capacity > 0
                and not hard_block
            )

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
    db: AsyncSession,
    *,
    service_id: int,
    start_date: date | None = None,
) -> ServiceAvailabilityResponse:
    """
    Детальная информация о доступности курса по всем его занятиям.

    Используется для pre‑check перед оплатой (модалка с календарём).
    """
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    if service.type != ServiceType.COURSE:
        raise HTTPException(status_code=400, detail="Услуга не является курсом")

    # Общая агрегация (can_book, requires_warning, message)
    availability = await check_course_availability(
        db,
        service_id=service_id,
        for_update=False,
    )

    stats = await _get_course_slots_with_capacity(db, service=service)
    if start_date is not None:
        stats = [
            s
            for s in stats
            if s.slot.start_time.date() >= start_date
        ]

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

