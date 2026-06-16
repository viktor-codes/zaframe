"""Single-entity booking lookups."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence


class BookingGetMixin:
    _session: AsyncSession

    @staticmethod
    def _active_pending_hold_clause(*, now: datetime) -> ColumnElement[bool]:
        from app.core.datetime_utils import ensure_utc

        now_utc = ensure_utc(now)
        return and_(
            Booking.status == BookingStatus.PENDING,
            Booking.reserved_until.is_not(None),
            Booking.reserved_until > now_utc,
        )

    async def get_by_id(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_occurrence(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking)
            .options(selectinload(Booking.occurrence))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_occurrence_and_studio(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking)
            .options(selectinload(Booking.occurrence).selectinload(Occurrence.studio))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_occurrence_and_guest_email(
        self,
        occurrence_id: int,
        guest_email: str,
    ) -> Booking | None:
        normalized_email = guest_email.strip().lower()
        result = await self._session.execute(
            select(Booking).where(
                Booking.occurrence_id == occurrence_id,
                func.lower(Booking.guest_email) == normalized_email,
                Booking.status.in_(BookingStatus.ACTIVE_STATUSES),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_occurrence_and_user_id(
        self,
        occurrence_id: int,
        user_id: int,
    ) -> Booking | None:
        result = await self._session.execute(
            select(Booking).where(
                Booking.occurrence_id == occurrence_id,
                Booking.user_id == user_id,
                Booking.status.in_(BookingStatus.ACTIVE_STATUSES),
            )
        )
        return result.scalar_one_or_none()
