"""Business logic for Occurrence (schedulable sessions)."""

from datetime import datetime

import structlog

from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.occurrence import Occurrence, OccurrenceStatus
from app.models.studio_member import StudioMemberRole
from app.modules.catalog.occurrence.schemas import OccurrenceCreate, OccurrenceUpdate

logger = structlog.get_logger(__name__)


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
    instructor_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: str | None = None,
) -> list[Occurrence]:
    return await uow.occurrences.list_(
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        instructor_id=instructor_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )


async def get_occurrences_count(
    uow: UnitOfWork,
    *,
    studio_id: int | None = None,
    instructor_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: str | None = None,
) -> int:
    return await uow.occurrences.count(
        studio_id=studio_id,
        instructor_id=instructor_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )


async def get_my_instructor_occurrences(
    uow: UnitOfWork,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: str | None = None,
) -> list[Occurrence]:
    return await uow.occurrences.list_for_instructor_user(
        user_id=user_id,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )


async def get_my_instructor_occurrences_count(
    uow: UnitOfWork,
    *,
    user_id: int,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    status: str | None = None,
) -> int:
    return await uow.occurrences.count_for_instructor_user(
        user_id=user_id,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )


async def _validate_instructor_assignment(
    uow: UnitOfWork,
    *,
    studio_id: int,
    instructor_id: int | None,
) -> None:
    if instructor_id is None:
        return
    instructor = await uow.studio_members.get_by_id(instructor_id)
    if instructor is None:
        raise NotFoundError("Instructor not found")
    if instructor.studio_id != studio_id or instructor.role != StudioMemberRole.INSTRUCTOR.value:
        raise ValidationError("Instructor must be an instructor member of this studio")


async def create_occurrence(uow: UnitOfWork, schema: OccurrenceCreate) -> Occurrence:
    if schema.end_time <= schema.start_time:
        raise ValidationError("End time must be after start time")
    if await uow.studios.get_by_id(schema.studio_id) is None:
        raise NotFoundError("Studio not found")
    service = await uow.services.get_by_studio_and_id(schema.studio_id, schema.service_id)
    if service is None:
        raise NotFoundError("Service not found in this studio")
    await _validate_instructor_assignment(
        uow,
        studio_id=schema.studio_id,
        instructor_id=schema.instructor_id,
    )

    occurrence = Occurrence(
        studio_id=schema.studio_id,
        service_id=schema.service_id,
        instructor_id=schema.instructor_id,
        start_time=ensure_utc(schema.start_time),
        end_time=ensure_utc(schema.end_time),
        title=schema.title,
        description=schema.description,
        max_capacity=schema.max_capacity,
        price_cents=schema.price_cents,
    )
    occurrence = await uow.occurrences.add(occurrence)
    log_domain_event(
        logger,
        "occurrence_generated",
        studio_id=occurrence.studio_id,
        service_id=occurrence.service_id,
        occurrence_id=occurrence.id,
    )
    return occurrence


async def update_occurrence(
    uow: UnitOfWork,
    occurrence: Occurrence,
    schema: OccurrenceUpdate,
) -> Occurrence:
    update_data = schema.model_dump(exclude_unset=True)
    old_status = occurrence.status
    if "status" in update_data and update_data["status"] not in (
        OccurrenceStatus.SCHEDULED,
        OccurrenceStatus.CANCELLED,
        OccurrenceStatus.COMPLETED,
    ):
        raise ValidationError("Invalid occurrence status")
    start_time = update_data.get("start_time", occurrence.start_time)
    end_time = update_data.get("end_time", occurrence.end_time)
    if end_time <= start_time:
        raise ValidationError("End time must be after start time")
    if "instructor_id" in update_data:
        await _validate_instructor_assignment(
            uow,
            studio_id=occurrence.studio_id,
            instructor_id=update_data["instructor_id"],
        )
    for field, value in update_data.items():
        if field in ("start_time", "end_time") and value is not None:
            value = ensure_utc(value)
        setattr(occurrence, field, value)
    if update_data.get("status") == OccurrenceStatus.CANCELLED:
        occurrence.cancelled_at = occurrence.cancelled_at or utc_now()
    elif update_data.get("status") == OccurrenceStatus.SCHEDULED:
        occurrence.cancelled_at = None
        occurrence.cancellation_reason = None
    occurrence = await uow.occurrences.save(occurrence)
    event = (
        "occurrence_cancelled"
        if old_status != OccurrenceStatus.CANCELLED
        and occurrence.status == OccurrenceStatus.CANCELLED
        else "occurrence_updated"
    )
    log_domain_event(
        logger,
        event,
        studio_id=occurrence.studio_id,
        service_id=occurrence.service_id,
        occurrence_id=occurrence.id,
        updated_fields=sorted(update_data.keys()),
        old_status=old_status if old_status != occurrence.status else None,
        status=occurrence.status,
    )
    return occurrence


async def delete_occurrence(uow: UnitOfWork, occurrence: Occurrence) -> None:
    bookings_count = await uow.bookings.count_by_occurrence(occurrence.id)
    if bookings_count > 0:
        occurrence.status = OccurrenceStatus.CANCELLED
        occurrence.cancelled_at = occurrence.cancelled_at or utc_now()
        if occurrence.cancellation_reason is None:
            occurrence.cancellation_reason = (
                "Cancelled because deletion was requested with bookings"
            )
        await uow.occurrences.save(occurrence)
        log_domain_event(
            logger,
            "occurrence_cancelled",
            studio_id=occurrence.studio_id,
            service_id=occurrence.service_id,
            occurrence_id=occurrence.id,
            bookings_count=bookings_count,
        )
        return
    await uow.occurrences.delete(occurrence)
