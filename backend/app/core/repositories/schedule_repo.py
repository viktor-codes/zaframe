"""
Репозиторий для сущности Schedule.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, schedule_id: int) -> Schedule | None:
        result = await self._session.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def list_by_service_id(self, service_id: int) -> list[Schedule]:
        result = await self._session.execute(
            select(Schedule)
            .where(Schedule.service_id == service_id)
            .order_by(Schedule.day_of_week, Schedule.start_time)
        )
        return list(result.scalars().all())
