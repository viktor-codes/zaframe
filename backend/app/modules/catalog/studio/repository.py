"""
Repository for the Studio entity.

Studio queries with filters and by slug for the public page.
"""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.core.datetime_utils import utc_now
from app.core.repository import WriteRepositoryMixin
from app.models.occurrence import Occurrence, OccurrenceStatus
from app.models.service import Service, ServiceVisibility
from app.models.studio import Studio
from app.models.studio_member import StudioMember


class StudioRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, studio_id: int) -> Studio | None:
        result = await self._session.execute(select(Studio).where(Studio.id == studio_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Studio | None:
        result = await self._session.execute(select(Studio).where(Studio.slug == slug))
        return result.scalar_one_or_none()

    async def get_by_stripe_account_id(self, stripe_account_id: str) -> Studio | None:
        result = await self._session.execute(
            select(Studio).where(Studio.stripe_account_id == stripe_account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug_with_services_occurrences(
        self, slug: str, *, is_active: bool = True
    ) -> Studio | None:
        """
        Load a public studio with services and upcoming scheduled occurrences only.

        WHY: loading every historical occurrence for a busy studio blows up memory
        and response time on the public storefront aggregate.
        """
        now_utc = utc_now()
        result = await self._session.execute(
            select(Studio)
            .options(
                selectinload(Studio.services).selectinload(
                    Service.occurrences.and_(
                        Occurrence.start_time >= now_utc,
                        Occurrence.status == OccurrenceStatus.SCHEDULED,
                    )
                ),
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
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
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
        conditions: list[ColumnElement[bool]],
        *,
        category: str | None = None,
        query: str | None = None,
    ) -> list[ColumnElement[bool]]:
        join_conditions = list(conditions)
        join_conditions.append(Service.studio_id == Studio.id)
        join_conditions.append(Service.is_active.is_(True))
        join_conditions.append(Service.visibility == ServiceVisibility.PUBLISHED)
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
        return result.scalar_one()


class StudioMemberRepository(WriteRepositoryMixin):
    """Repository for per-studio membership roles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, member_id: int) -> StudioMember | None:
        result = await self._session.execute(
            select(StudioMember).where(StudioMember.id == member_id)
        )
        return result.scalar_one_or_none()

    async def get_by_studio_and_user(
        self,
        *,
        studio_id: int,
        user_id: int,
    ) -> StudioMember | None:
        result = await self._session.execute(
            select(StudioMember).where(
                StudioMember.studio_id == studio_id,
                StudioMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, *, user_id: int) -> list[StudioMember]:
        result = await self._session.execute(
            select(StudioMember)
            .options(selectinload(StudioMember.studio))
            .where(StudioMember.user_id == user_id)
            .order_by(StudioMember.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_for_studio(self, *, studio_id: int) -> list[StudioMember]:
        result = await self._session.execute(
            select(StudioMember)
            .options(selectinload(StudioMember.user))
            .where(StudioMember.studio_id == studio_id)
            .order_by(StudioMember.created_at.desc())
        )
        return list(result.scalars().all())
