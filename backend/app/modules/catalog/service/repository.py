"""
Репозиторий для сущности Service.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service import Service
from app.repositories.base import WriteRepositoryMixin


class ServiceRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, service_id: int) -> Service | None:
        result = await self._session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_occurrences(self, service_id: int) -> Service | None:
        result = await self._session.execute(
            select(Service).options(selectinload(Service.occurrences)).where(Service.id == service_id)
        )
        return result.scalar_one_or_none()

    async def get_by_studio_and_id(self, studio_id: int, service_id: int) -> Service | None:
        result = await self._session.execute(
            select(Service).where(
                Service.id == service_id,
                Service.studio_id == studio_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_active_by_studio_ids(
        self,
        studio_ids: list[int],
        *,
        category: str | None = None,
    ) -> list[Service]:
        query = select(Service).where(
            Service.studio_id.in_(studio_ids),
            Service.is_active.is_(True),
        )
        if category is not None:
            query = query.where(Service.category == category)
        result = await self._session.execute(query)
        return list(result.scalars().all())
