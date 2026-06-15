"""Repository for Occurrence entities."""

# WHY: global lock order to prevent deadlocks — all FOR UPDATE on occurrences
# must use ORDER BY occurrences.id ASC (see get_by_id_for_update, list_*_for_update).

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime_utils import ensure_utc
from app.models.occurrence import Occurrence, OccurrenceStatus
from app.repositories.base import WriteRepositoryMixin


class OccurrenceRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, occurrence_id: int) -> Occurrence | None:
        result = await self._session.execute(
            select(Occurrence).where(Occurrence.id == occurrence_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, occurrence_id: int) -> Occurrence | None:
        result = await self._session.execute(
            select(Occurrence).where(Occurrence.id == occurrence_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        studio_id: int | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        status: str | None = None,
    ) -> list[Occurrence]:
        query = select(Occurrence)
        if studio_id is not None:
            query = query.where(Occurrence.studio_id == studio_id)
        if start_from is not None:
            query = query.where(Occurrence.start_time >= ensure_utc(start_from))
        if start_to is not None:
            query = query.where(Occurrence.start_time <= ensure_utc(start_to))
        if status is not None:
            query = query.where(Occurrence.status == status)
        query = query.offset(skip).limit(limit).order_by(Occurrence.start_time.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        studio_id: int | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        status: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(Occurrence)
        if studio_id is not None:
            query = query.where(Occurrence.studio_id == studio_id)
        if start_from is not None:
            query = query.where(Occurrence.start_time >= ensure_utc(start_from))
        if start_to is not None:
            query = query.where(Occurrence.start_time <= ensure_utc(start_to))
        if status is not None:
            query = query.where(Occurrence.status == status)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def list_by_service_active(self, service_id: int) -> list[Occurrence]:
        query = (
            select(Occurrence)
            .where(
                Occurrence.service_id == service_id,
                Occurrence.status == OccurrenceStatus.ACTIVE,
            )
            .order_by(Occurrence.start_time.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_active_future_by_service(
        self,
        service_id: int,
        *,
        now: datetime,
    ) -> list[Occurrence]:
        query = (
            select(Occurrence)
            .where(
                Occurrence.service_id == service_id,
                Occurrence.status == OccurrenceStatus.ACTIVE,
                Occurrence.start_time >= ensure_utc(now),
            )
            .order_by(Occurrence.id.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_active_future_by_service_for_update(
        self,
        service_id: int,
        *,
        now: datetime,
    ) -> list[Occurrence]:
        # WHY: global lock order to prevent deadlocks
        query = (
            select(Occurrence)
            .where(
                Occurrence.service_id == service_id,
                Occurrence.status == OccurrenceStatus.ACTIVE,
                Occurrence.start_time >= ensure_utc(now),
            )
            .with_for_update()
            .order_by(Occurrence.id.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_by_service_active_for_update(self, service_id: int) -> list[Occurrence]:
        # WHY: global lock order to prevent deadlocks
        query = (
            select(Occurrence)
            .where(
                Occurrence.service_id == service_id,
                Occurrence.status == OccurrenceStatus.ACTIVE,
            )
            .with_for_update()
            .order_by(Occurrence.id.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_overlapping(
        self,
        studio_id: int,
        service_id: int,
        min_start: datetime,
        max_end: datetime,
    ) -> list[Occurrence]:
        min_start_utc = ensure_utc(min_start)
        max_end_utc = ensure_utc(max_end)
        result = await self._session.execute(
            select(Occurrence).where(
                Occurrence.studio_id == studio_id,
                Occurrence.service_id == service_id,
                Occurrence.start_time < max_end_utc,
                Occurrence.end_time > min_start_utc,
            )
        )
        return list(result.scalars().all())
