"""Booking list and filter queries."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.booking import Booking
from app.models.occurrence import Occurrence
from app.models.studio import Studio
from app.modules.booking.repository.get import BookingGetMixin


class BookingListQueriesMixin(BookingGetMixin):
    _session: AsyncSession

    @staticmethod
    def _studio_owner_clause(*, owner_id: int) -> ColumnElement[bool]:
        return Studio.owner_id == owner_id

    async def list_for_studio_owner(
        self,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 20,
        occurrence_id: int | None = None,
        status: str | None = None,
    ) -> list[Booking]:
        query = (
            select(Booking)
            .join(Booking.occurrence)
            .join(Occurrence.studio)
            .where(self._studio_owner_clause(owner_id=owner_id))
        )
        if occurrence_id is not None:
            query = query.where(Booking.occurrence_id == occurrence_id)
        if status is not None:
            query = query.where(Booking.status == status)
        query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_for_studio_owner(
        self,
        *,
        owner_id: int,
        occurrence_id: int | None = None,
        status: str | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(Booking)
            .join(Booking.occurrence)
            .join(Occurrence.studio)
            .where(self._studio_owner_clause(owner_id=owner_id))
        )
        if occurrence_id is not None:
            query = query.where(Booking.occurrence_id == occurrence_id)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self._session.execute(query)
        return result.scalar_one()

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
