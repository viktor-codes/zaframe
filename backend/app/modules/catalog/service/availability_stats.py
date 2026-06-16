"""Internal helpers for loading and evaluating course capacity stats."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.datetime_utils import utc_now
from app.core.uow import UnitOfWork
from app.models import Occurrence, Service
from app.modules.catalog.capacity import (
    OccurrenceFill,
    classify_occurrence_capacity,
    evaluate_course_capacity_summary,
    is_occurrence_overbooked,
)
from app.modules.catalog.service.dto import (
    CourseAvailabilityDTO,
    CourseBookingPreviewItemDTO,
)


@dataclass
class CapacityStats:
    occurrence: Occurrence
    confirmed_count: int
    pending_count: int

    @property
    def total(self) -> int:
        return self.confirmed_count + self.pending_count


async def get_course_occurrences_with_capacity(
    uow: UnitOfWork,
    *,
    service: Service,
    now: datetime | None = None,
) -> list[CapacityStats]:
    """Load active future course occurrences and their fill levels."""
    now_utc = now or utc_now()
    occurrences = await uow.occurrences.list_active_future_by_service(
        service.id,
        now=now_utc,
    )
    return await build_course_capacity_stats(uow, occurrences=occurrences, now=now_utc)


async def get_course_occurrences_with_capacity_for_update(
    uow: UnitOfWork,
    *,
    service: Service,
    now: datetime | None = None,
) -> list[CapacityStats]:
    """Lock active future course occurrences, then read fill levels for booking."""
    now_utc = now or utc_now()
    occurrences = await uow.occurrences.list_active_future_by_service_for_update(
        service.id,
        now=now_utc,
    )
    occurrences = sorted(occurrences, key=lambda o: o.start_time)
    return await build_course_capacity_stats(uow, occurrences=occurrences, now=now_utc)


async def build_course_capacity_stats(
    uow: UnitOfWork,
    *,
    occurrences: list[Occurrence],
    now: datetime,
) -> list[CapacityStats]:
    if not occurrences:
        return []

    occurrence_ids = [o.id for o in occurrences]
    counts_map = await uow.bookings.get_confirmed_pending_counts_by_occurrence_ids(
        occurrence_ids,
        now=now,
    )

    return [
        CapacityStats(
            occurrence=occurrence,
            confirmed_count=counts_map.get(occurrence.id, (0, 0))[0],
            pending_count=counts_map.get(occurrence.id, (0, 0))[1],
        )
        for occurrence in occurrences
    ]


def evaluate_course_availability(
    service: Service,
    stats: list[CapacityStats],
) -> CourseAvailabilityDTO:
    if not stats:
        return CourseAvailabilityDTO(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_occurrences=[],
            message="Course has no upcoming sessions",
        )

    fills = [
        OccurrenceFill(
            occurrence_id=s.occurrence.id,
            max_capacity=s.occurrence.max_capacity,
            confirmed_count=s.confirmed_count,
            pending_count=s.pending_count,
        )
        for s in stats
    ]
    summary = evaluate_course_capacity_summary(service, fills)

    overbooked_items: list[CourseBookingPreviewItemDTO] = []
    for s, fill in zip(stats, fills, strict=True):
        flags = classify_occurrence_capacity(
            service,
            max_capacity=fill.max_capacity,
            current_bookings=fill.current_total,
        )
        if not is_occurrence_overbooked(flags):
            continue
        overbooked_items.append(
            CourseBookingPreviewItemDTO(
                occurrence_id=s.occurrence.id,
                start_time=s.occurrence.start_time,
                max_capacity=fill.max_capacity,
                confirmed_count=fill.confirmed_count,
                pending_count=fill.pending_count,
                total_after_booking=flags.total_after_one_booking,
                is_over_soft_limit=flags.is_over_soft,
                is_over_hard_limit=flags.is_over_hard,
            )
        )

    if summary.hard_block:
        return CourseAvailabilityDTO(
            can_book=False,
            requires_warning=False,
            hard_block=True,
            overbooked_occurrences=overbooked_items,
            message="Not enough seats in several course sessions. Contact the studio owner.",
        )

    message = None
    if summary.requires_warning:
        message = "Some course sessions will be fuller, but booking is still allowed."

    return CourseAvailabilityDTO(
        can_book=summary.can_book,
        requires_warning=summary.requires_warning,
        hard_block=False,
        overbooked_occurrences=overbooked_items,
        message=message,
    )
