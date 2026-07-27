"""Booking list and filter queries."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.booking import Booking
from app.models.occurrence import Occurrence
from app.models.studio import Studio
from app.models.studio_member import StudioMember
from app.modules.booking.repository.get import BookingGetMixin


class BookingListQueriesMixin(BookingGetMixin):
    _session: AsyncSession

    @staticmethod
    def _studio_member_clause(*, user_id: int) -> ColumnElement[bool]:
        return or_(Studio.owner_id == user_id, StudioMember.user_id == user_id)

    async def list_for_studio_member(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        studio_id: int | None = None,
        occurrence_id: int | None = None,
        status: str | None = None,
    ) -> list[Booking]:
        query = (
            select(Booking)
            .options(selectinload(Booking.occurrence))
            .join(Booking.occurrence)
            .join(Occurrence.studio)
            .outerjoin(
                StudioMember,
                (StudioMember.studio_id == Studio.id) & (StudioMember.user_id == user_id),
            )
            .where(self._studio_member_clause(user_id=user_id))
            .distinct()
        )
        if studio_id is not None:
            query = query.where(Occurrence.studio_id == studio_id)
        if occurrence_id is not None:
            query = query.where(Booking.occurrence_id == occurrence_id)
        if status is not None:
            query = query.where(Booking.status == status)
        query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_for_studio_member(
        self,
        *,
        user_id: int,
        studio_id: int | None = None,
        occurrence_id: int | None = None,
        status: str | None = None,
    ) -> int:
        # WHY: outerjoin on studio_members can duplicate rows; count distinct booking ids.
        query = (
            select(func.count(func.distinct(Booking.id)))
            .select_from(Booking)
            .join(Booking.occurrence)
            .join(Occurrence.studio)
            .outerjoin(
                StudioMember,
                (StudioMember.studio_id == Studio.id) & (StudioMember.user_id == user_id),
            )
            .where(self._studio_member_clause(user_id=user_id))
        )
        if studio_id is not None:
            query = query.where(Occurrence.studio_id == studio_id)
        if occurrence_id is not None:
            query = query.where(Booking.occurrence_id == occurrence_id)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_my_with_occurrence_and_studio(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        user_id: int,
        user_email: str,
        include_guest_email: bool = True,
    ) -> list[Booking]:
        query = (
            select(Booking)
            .options(
                selectinload(Booking.occurrence).selectinload(Occurrence.studio),
            )
            .where(
                (Booking.user_id == user_id)
                | ((Booking.guest_email == user_email) if include_guest_email else False)
            )
            .order_by(Booking.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_my_with_occurrence_and_studio(
        self,
        *,
        user_id: int,
        user_email: str,
        include_guest_email: bool = True,
    ) -> int:
        query = (
            select(func.count())
            .select_from(Booking)
            .where(
                (Booking.user_id == user_id)
                | ((Booking.guest_email == user_email) if include_guest_email else False)
            )
        )
        result = await self._session.execute(query)
        return result.scalar_one()

    async def list_(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        occurrence_id: int | None = None,
        user_id: int | None = None,
        guest_email: str | None = None,
        status: str | None = None,
        order_id: int | None = None,
    ) -> list[Booking]:
        query = select(Booking)
        if occurrence_id is not None:
            query = query.where(Booking.occurrence_id == occurrence_id)
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        if guest_email is not None:
            query = query.where(Booking.guest_email == guest_email)
        if status is not None:
            query = query.where(Booking.status == status)
        if order_id is not None:
            query = query.where(Booking.order_id == order_id)
        query = query.offset(skip).limit(limit).order_by(Booking.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        occurrence_id: int | None = None,
        user_id: int | None = None,
        guest_email: str | None = None,
        status: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(Booking)
        if occurrence_id is not None:
            query = query.where(Booking.occurrence_id == occurrence_id)
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        if guest_email is not None:
            query = query.where(Booking.guest_email == guest_email)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self._session.execute(query)
        return result.scalar_one()
