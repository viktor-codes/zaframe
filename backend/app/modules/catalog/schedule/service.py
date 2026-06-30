"""
Business logic for ScheduleTemplate rows and Occurrence generation.

This module owns:
- ScheduleTemplate CRUD
- Occurrence generation from schedule parameters
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
    """Create a schedule template for a service."""
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
    """Get all schedule templates for a service."""
    return await uow.schedule_templates.list_by_service_id(service_id)


async def get_schedule_template(
    uow: UnitOfWork, schedule_template_id: int
) -> ScheduleTemplate | None:
    """Get one schedule template."""
    return await uow.schedule_templates.get_by_id(schedule_template_id)


async def delete_schedule_template(uow: UnitOfWork, schedule: ScheduleTemplate) -> None:
    """Delete a schedule template."""
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
    """Get a schedule template or raise NotFoundError."""
    schedule = await uow.schedule_templates.get_by_id(schedule_template_id)
    if schedule is None:
        raise NotFoundError("ScheduleTemplate not found")
    return schedule


def _iterate_weeks(start: date, weeks_count: int) -> Iterable[date]:
    """Generate week-start dates on Mondays for the requested number of weeks."""
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
    Generate course occurrences.

    Used by:
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

    # Normalize start_date to the closest previous Monday for simple week iteration.
    start_monday = start_date - timedelta(days=start_date.weekday())

    # Compute every planned interval first, then query overlaps once to avoid
    # creating dead sessions during repeated generation.
    planned_intervals: list[tuple[datetime, datetime]] = []
    duration = timedelta(minutes=service.duration_minutes)

    for week_start in _iterate_weeks(start_monday, weeks_count):
        for dow in days:
            if not 0 <= dow <= 6:
                raise ValidationError("day_of_week must be between 0 and 6")
            day_date = week_start + timedelta(days=dow)
            if day_date < start_date:
                # Skip sessions before the requested start date.
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
