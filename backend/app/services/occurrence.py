"""Business logic for Occurrence (schedulable sessions)."""

from datetime import datetime

from app.core.datetime_utils import ensure_utc
from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.occurrence import Occurrence, OccurrenceStatus
from app.schemas.occurrence import OccurrenceCreate, OccurrenceUpdate


async def get_occurrence(uow: UnitOfWork, occurrence_id: int) -> Occurrence | None:
    return await uow.occurrences.get_by_id(occurrence_id)


async def get_occurrence_or_raise(uow: UnitOfWork, occurrence_id: int) -> Occurrence:
    occurrence = await uow.occurrences.get_by_id(occurrence_id)
    if occurrence is None:
        raise NotFoundError("Occurrence not found")
    return occurrence


async def get_occurrences(
    uow: UnitOfWork,
    *,
    skip: int = 0,
    limit: int = 20,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: str | None = None,
) -> list[Occurrence]:
    return await uow.occurrences.list_(
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )


async def get_occurrences_count(
    uow: UnitOfWork,
    *,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: str | None = None,
) -> int:
    return await uow.occurrences.count(
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )


async def get_bookings_count(uow: UnitOfWork, occurrence_id: int) -> int:
    return await uow.bookings.count_confirmed_by_occurrence(occurrence_id)


async def create_occurrence(uow: UnitOfWork, schema: OccurrenceCreate) -> Occurrence:
    if schema.end_time <= schema.start_time:
        raise ValidationError("End time must be after start time")
    if await uow.studios.get_by_id(schema.studio_id) is None:
        raise NotFoundError("Studio not found")

    occurrence = Occurrence(
        studio_id=schema.studio_id,
        service_id=schema.service_id,
        start_time=ensure_utc(schema.start_time),
        end_time=ensure_utc(schema.end_time),
        title=schema.title,
        description=schema.description,
        max_capacity=schema.max_capacity,
        price_cents=schema.price_cents,
    )
    return await uow.occurrences.add(occurrence)


async def update_occurrence(
    uow: UnitOfWork,
    occurrence: Occurrence,
    schema: OccurrenceUpdate,
) -> Occurrence:
    update_data = schema.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] not in (
        OccurrenceStatus.ACTIVE,
        OccurrenceStatus.CANCELLED,
    ):
        raise ValidationError("Invalid occurrence status")
    start_time = update_data.get("start_time", occurrence.start_time)
    end_time = update_data.get("end_time", occurrence.end_time)
    if end_time <= start_time:
        raise ValidationError("End time must be after start time")
    for field, value in update_data.items():
        if field in ("start_time", "end_time") and value is not None:
            value = ensure_utc(value)
        setattr(occurrence, field, value)
    return await uow.occurrences.save(occurrence)


async def delete_occurrence(uow: UnitOfWork, occurrence: Occurrence) -> None:
    await uow.occurrences.delete(occurrence)
