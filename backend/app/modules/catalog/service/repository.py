"""Repository for the Service entity."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repository import WriteRepositoryMixin
from app.models.service import Service, ServiceVisibility


class ServiceRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, service_id: int) -> Service | None:
        result = await self._session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_occurrences(self, service_id: int) -> Service | None:
        result = await self._session.execute(
            select(Service)
            .options(selectinload(Service.occurrences))
            .where(Service.id == service_id)
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

    async def list_by_studio(
        self,
        studio_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[Service]:
        query = select(Service).where(Service.studio_id == studio_id)
        if is_active is not None:
            query = query.where(Service.is_active.is_(is_active))
        query = query.order_by(Service.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_by_studio(
        self,
        studio_id: int,
        *,
        is_active: bool | None = None,
    ) -> int:
        query = select(func.count()).select_from(Service).where(Service.studio_id == studio_id)
        if is_active is not None:
            query = query.where(Service.is_active.is_(is_active))
        result = await self._session.execute(query)
        return result.scalar_one()

    async def list_active_by_studio_ids(
        self,
        studio_ids: list[int],
        *,
        category: str | None = None,
    ) -> list[Service]:
        query = select(Service).where(
            Service.studio_id.in_(studio_ids),
            Service.is_active.is_(True),
            Service.visibility == ServiceVisibility.PUBLISHED,
        )
        if category is not None:
            query = query.where(Service.category == category)
        result = await self._session.execute(query)
        return list(result.scalars().all())
