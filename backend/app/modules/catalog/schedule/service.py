"""
Бизнес-логика для ScheduleTemplate и генерации occurrence'ов (Occurrence).

Здесь живут:
- CRUD шаблонов расписания (ScheduleTemplate)
- генерация occurrence'ов на основе параметров расписания
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta

from app.core.datetime_utils import studio_local_date_now, studio_local_to_utc
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models import Occurrence, ScheduleTemplate
from app.modules.catalog.schedule.schemas import ScheduleTemplateCreate, ScheduleTemplateUpdate


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


async def get_schedule_template(
    uow: UnitOfWork, schedule_template_id: int
) -> ScheduleTemplate | None:
    """Получить один шаблон расписания."""
    return await uow.schedule_templates.get_by_id(schedule_template_id)


async def delete_schedule_template(uow: UnitOfWork, schedule: ScheduleTemplate) -> None:
    """Удалить шаблон расписания."""
    await uow.schedule_templates.delete(schedule)


async def update_schedule_template(
    uow: UnitOfWork,
    schedule: ScheduleTemplate,
    schema: ScheduleTemplateUpdate,
) -> ScheduleTemplate:
    """Update schedule template metadata without mutating generated occurrences."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    return await uow.schedule_templates.save(schedule)


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
    POST /studios/{id}/generate-occurrences
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

    existing_occurrences = await uow.occurrences.list_overlapping(
        studio_id, service_id, min_start, max_end
    )

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
