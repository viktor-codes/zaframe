"""Capacity counts, lifecycle queries, and guest attach updates."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.core.datetime_utils import ensure_utc, utc_now
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence
from app.modules.booking.repository.get import BookingGetMixin


class BookingCapacityQueriesMixin(BookingGetMixin):
    _session: AsyncSession

    async def count_confirmed_by_occurrence(self, occurrence_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.occurrence_id == occurrence_id,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        return result.scalar_one()

    async def count_pending_by_occurrence(
        self,
        occurrence_id: int,
        *,
        now: datetime | None = None,
        exclude_booking_id: int | None = None,
    ) -> int:
        now_utc = now or utc_now()
        conditions: list[ColumnElement[bool]] = [
            Booking.occurrence_id == occurrence_id,
            self._active_pending_hold_clause(now=now_utc),
        ]
        if exclude_booking_id is not None:
            conditions.append(Booking.id != exclude_booking_id)
        result = await self._session.execute(
            select(func.count()).select_from(Booking).where(*conditions)
        )
        return result.scalar_one()

    async def list_stale_pending(self, *, now: datetime | None = None) -> list[Booking]:
        now_utc = ensure_utc(now or utc_now())
        result = await self._session.execute(
            select(Booking).where(
                Booking.status == BookingStatus.PENDING,
                or_(
                    Booking.reserved_until.is_(None),
                    Booking.reserved_until <= now_utc,
                ),
            )
        )
        return list(result.scalars().all())

    async def list_past_confirmed(self, *, now: datetime | None = None) -> list[Booking]:
        now_utc = ensure_utc(now or utc_now())
        result = await self._session.execute(
            select(Booking)
            .join(Booking.occurrence)
            .where(
                Booking.status == BookingStatus.CONFIRMED,
                Occurrence.end_time < now_utc,
            )
        )
        return list(result.scalars().all())

    async def get_confirmed_pending_counts_by_occurrence_ids(
        self, occurrence_ids: list[int], *, now: datetime | None = None
    ) -> dict[int, tuple[int, int]]:
        if not occurrence_ids:
            return {}
        now_utc = now or utc_now()
        counts_q = (
            select(
                Booking.occurrence_id,
                func.sum(
                    case(
                        (Booking.status == BookingStatus.CONFIRMED, 1),
                        else_=0,
                    )
                ).label("confirmed"),
                func.sum(
                    case(
                        (self._active_pending_hold_clause(now=now_utc), 1),
                        else_=0,
                    )
                ).label("pending"),
            )
            .where(Booking.occurrence_id.in_(occurrence_ids))
            .group_by(Booking.occurrence_id)
        )
        result = await self._session.execute(counts_q)
        return {row.occurrence_id: (row.confirmed or 0, row.pending or 0) for row in result}

    async def attach_guest_bookings_by_email(
        self,
        *,
        user_id: int,
        guest_email: str,
        booking_id: int | None = None,
    ) -> int:
        normalized_email = guest_email.strip().lower()
        conditions = [
            Booking.user_id.is_(None),
            func.lower(Booking.guest_email) == normalized_email,
        ]
        if booking_id is not None:
            conditions.append(Booking.id == booking_id)

        result = await self._session.execute(
            update(Booking).where(*conditions).values(user_id=user_id)
        )
        await self._session.flush()
        cursor = cast(CursorResult[Any], result)
        return cursor.rowcount or 0
