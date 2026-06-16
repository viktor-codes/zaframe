"""Repository for ScheduleTemplate entities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import WriteRepositoryMixin
from app.models.schedule_template import ScheduleTemplate


class ScheduleTemplateRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, schedule_template_id: int) -> ScheduleTemplate | None:
        result = await self._session.execute(
            select(ScheduleTemplate).where(ScheduleTemplate.id == schedule_template_id)
        )
        return result.scalar_one_or_none()

    async def list_by_service_id(self, service_id: int) -> list[ScheduleTemplate]:
        result = await self._session.execute(
            select(ScheduleTemplate)
            .where(ScheduleTemplate.service_id == service_id)
            .order_by(ScheduleTemplate.day_of_week, ScheduleTemplate.start_time)
        )
        return list(result.scalars().all())
