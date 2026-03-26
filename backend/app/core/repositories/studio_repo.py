"""
Репозиторий для сущности Studio.

Выборки студий с фильтрами и по slug (для публичной страницы).
"""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.service import Service
from app.models.studio import Studio


class StudioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, studio_id: int) -> Studio | None:
        result = await self._session.execute(select(Studio).where(Studio.id == studio_id))
        return result.scalar_one_or_none()

    async def get_by_slug_with_services_slots(
        self, slug: str, *, is_active: bool = True
    ) -> Studio | None:
        result = await self._session.execute(
            select(Studio)
            .options(
                selectinload(Studio.services).selectinload(Service.slots),
            )
            .where(
                Studio.slug == slug,
                Studio.is_active.is_(is_active),
            )
        )
        return result.scalar_one_or_none()

    def _list_conditions(
        self,
        *,
        owner_id: int | None = None,
        is_active: bool | None = None,
        city: str | None = None,
        category: str | None = None,
        query: str | None = None,
        amenities: list[str] | None = None,
    ) -> list:
        conditions = []
        if owner_id is not None:
            conditions.append(Studio.owner_id == owner_id)
        if is_active is not None:
            conditions.append(Studio.is_active == is_active)
        if city:
            city_norm = city.strip().lower()
            if city_norm:
                conditions.append(func.lower(Studio.city) == city_norm)
        if amenities:
            for a in amenities:
                if a and a.strip():
                    conditions.append(Studio.amenities.contains([a.strip()]))
        return conditions

    def _join_conditions(
        self,
        conditions: list,
        *,
        category: str | None = None,
        query: str | None = None,
    ) -> list:
        join_conditions = list(conditions)
        join_conditions.append(Service.studio_id == Studio.id)
        join_conditions.append(Service.is_active.is_(True))
        if category:
            join_conditions.append(Service.category == category)
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            join_conditions.append(
                or_(
                    Studio.name.ilike(pattern),
                    Service.name.ilike(pattern),
                )
            )
        return join_conditions

    async def list_(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        owner_id: int | None = None,
        is_active: bool | None = None,
        city: str | None = None,
        category: str | None = None,
        query: str | None = None,
        amenities: list[str] | None = None,
    ) -> list[Studio]:
        conditions = self._list_conditions(
            owner_id=owner_id,
            is_active=is_active,
            city=city,
            amenities=amenities,
        )
        need_join = category or (query and query.strip())
        if need_join:
            join_conditions = self._join_conditions(conditions, category=category, query=query)
            subq = (
                select(Studio.id)
                .join(Service, Service.studio_id == Studio.id)
                .where(and_(*join_conditions))
                .distinct()
            )
            stmt = (
                select(Studio)
                .where(Studio.id.in_(subq))
                .order_by(Studio.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
        else:
            stmt = select(Studio)
            if conditions:
                stmt = stmt.where(*conditions)
            stmt = stmt.order_by(Studio.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        owner_id: int | None = None,
        is_active: bool | None = None,
        city: str | None = None,
        category: str | None = None,
        query: str | None = None,
        amenities: list[str] | None = None,
    ) -> int:
        conditions = self._list_conditions(
            owner_id=owner_id,
            is_active=is_active,
            city=city,
            amenities=amenities,
        )
        need_join = category or (query and query.strip())
        if need_join:
            join_conditions = self._join_conditions(conditions, category=category, query=query)
            subq = (
                select(Studio.id)
                .join(Service, Service.studio_id == Studio.id)
                .where(and_(*join_conditions))
                .distinct()
            )
            stmt = select(func.count()).select_from(subq.subquery())
        else:
            stmt = select(func.count()).select_from(Studio)
            if conditions:
                stmt = stmt.where(*conditions)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0
