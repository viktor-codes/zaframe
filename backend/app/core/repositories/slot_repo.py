"""
Репозиторий для сущности Slot.
"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slot import Slot


def _to_naive_utc(dt: datetime) -> datetime:
    from datetime import timezone
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class SlotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, slot_id: int) -> Slot | None:
        result = await self._session.execute(select(Slot).where(Slot.id == slot_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, slot_id: int) -> Slot | None:
        result = await self._session.execute(
            select(Slot).where(Slot.id == slot_id).with_for_update()
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
        is_active: bool | None = None,
    ) -> list[Slot]:
        query = select(Slot)
        if studio_id is not None:
            query = query.where(Slot.studio_id == studio_id)
        if start_from is not None:
            query = query.where(Slot.start_time >= _to_naive_utc(start_from))
        if start_to is not None:
            query = query.where(Slot.start_time <= _to_naive_utc(start_to))
        if is_active is not None:
            query = query.where(Slot.is_active == is_active)
        query = query.offset(skip).limit(limit).order_by(Slot.start_time.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        studio_id: int | None = None,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        is_active: bool | None = None,
    ) -> int:
        query = select(func.count()).select_from(Slot)
        if studio_id is not None:
            query = query.where(Slot.studio_id == studio_id)
        if start_from is not None:
            query = query.where(Slot.start_time >= _to_naive_utc(start_from))
        if start_to is not None:
            query = query.where(Slot.start_time <= _to_naive_utc(start_to))
        if is_active is not None:
            query = query.where(Slot.is_active == is_active)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() or 0

    async def list_by_service_active(
        self, service_id: int, *, for_update: bool = False
    ) -> list[Slot]:
        query = select(Slot).where(
            Slot.service_id == service_id,
            Slot.status == "active",
            Slot.is_active.is_(True),
        )
        if for_update:
            query = query.with_for_update()
        query = query.order_by(Slot.start_time.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_overlapping(
        self,
        studio_id: int,
        service_id: int,
        min_start: datetime,
        max_end: datetime,
    ) -> list[Slot]:
        """Слоты этого сервиса, пересекающиеся с интервалом [min_start, max_end]."""
        result = await self._session.execute(
            select(Slot).where(
                Slot.studio_id == studio_id,
                Slot.service_id == service_id,
                Slot.start_time < max_end,
                Slot.end_time > min_start,
            )
        )
        return list(result.scalars().all())
