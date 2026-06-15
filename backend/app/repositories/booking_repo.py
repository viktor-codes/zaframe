"""
Репозиторий для сущности Booking.

Все выборки по бронированиям инкапсулированы здесь.
"""

from datetime import datetime

from sqlalchemy import and_, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.core.datetime_utils import ensure_utc, utc_now
from app.models.booking import Booking, BookingStatus
from app.models.slot import Slot
from app.models.studio import Studio
from app.repositories.base import WriteRepositoryMixin


class BookingRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _active_pending_hold_clause(*, now: datetime) -> ColumnElement[bool]:
        """
        SQL WHERE fragment: pending bookings that still reserve slot capacity.

        WHY: legacy rows may have reserved_until=NULL; those holds must not lock seats forever.
        """
        now_utc = ensure_utc(now)
        return and_(
            Booking.status == BookingStatus.PENDING,
            Booking.reserved_until.is_not(None),
            Booking.reserved_until > now_utc,
        )

    async def get_by_id(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_slot(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking).options(selectinload(Booking.slot)).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_slot_and_studio(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking)
            .options(selectinload(Booking.slot).selectinload(Slot.studio))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _studio_owner_clause(*, owner_id: int) -> ColumnElement[bool]:
        return Studio.owner_id == owner_id

    async def list_for_studio_owner(
        self,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 20,
        slot_id: int | None = None,
        status: str | None = None,
    ) -> list[Booking]:
        query = (
            select(Booking)
            .join(Booking.slot)
            .join(Slot.studio)
            .where(self._studio_owner_clause(owner_id=owner_id))
        )
        if slot_id is not None:
            query = query.where(Booking.slot_id == slot_id)
        if status is not None:
            query = query.where(Booking.status == status)
        query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_for_studio_owner(
        self,
        *,
        owner_id: int,
        slot_id: int | None = None,
        status: str | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(Booking)
            .join(Booking.slot)
            .join(Slot.studio)
            .where(self._studio_owner_clause(owner_id=owner_id))
        )
        if slot_id is not None:
            query = query.where(Booking.slot_id == slot_id)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def list_my_with_slot_and_studio(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        user_id: int,
        user_email: str,
        include_guest_email: bool = True,
    ) -> list[Booking]:
        """
        List bookings for the current user with slot + studio preloaded (no N+1).

        include_guest_email=True makes the endpoint backward-compatible with guest bookings
        created before account activation (matched by guest_email == user.email).
        """
        query = (
            select(Booking)
            .options(
                selectinload(Booking.slot).selectinload(Slot.studio),
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
        slot_id: int | None = None,
        user_id: int | None = None,
        guest_email: str | None = None,
        status: str | None = None,
        order_id: int | None = None,
    ) -> list[Booking]:
        query = select(Booking)
        if slot_id is not None:
            query = query.where(Booking.slot_id == slot_id)
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
        slot_id: int | None = None,
        user_id: int | None = None,
        guest_email: str | None = None,
        status: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(Booking)
        if slot_id is not None:
            query = query.where(Booking.slot_id == slot_id)
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        if guest_email is not None:
            query = query.where(Booking.guest_email == guest_email)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_confirmed_by_slot(self, slot_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.slot_id == slot_id,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        return result.scalar_one()

    async def count_pending_by_slot(
        self,
        slot_id: int,
        *,
        now: datetime | None = None,
        exclude_booking_id: int | None = None,
    ) -> int:
        now_utc = now or utc_now()
        conditions: list[ColumnElement[bool]] = [
            Booking.slot_id == slot_id,
            self._active_pending_hold_clause(now=now_utc),
        ]
        if exclude_booking_id is not None:
            conditions.append(Booking.id != exclude_booking_id)
        result = await self._session.execute(
            select(func.count()).select_from(Booking).where(*conditions)
        )
        return result.scalar_one()

    async def get_active_by_slot_and_guest_email(
        self,
        slot_id: int,
        guest_email: str,
    ) -> Booking | None:
        """Non-cancelled booking for slot + guest email (case-insensitive)."""
        normalized_email = guest_email.strip().lower()
        result = await self._session.execute(
            select(Booking).where(
                Booking.slot_id == slot_id,
                func.lower(Booking.guest_email) == normalized_email,
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_slot_and_user_id(
        self,
        slot_id: int,
        user_id: int,
    ) -> Booking | None:
        """Non-cancelled booking for slot + registered user."""
        result = await self._session.execute(
            select(Booking).where(
                Booking.slot_id == slot_id,
                Booking.user_id == user_id,
                Booking.status != BookingStatus.CANCELLED,
            )
        )
        return result.scalar_one_or_none()

    async def attach_guest_bookings_by_email(
        self,
        *,
        user_id: int,
        guest_email: str,
        booking_id: int | None = None,
    ) -> int:
        """
        Set user_id on guest bookings where guest_email matches and user_id is NULL.

        When booking_id is set, only that booking is updated (still requires email match).
        Returns the number of rows updated.
        """
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
        return result.rowcount or 0

    async def get_confirmed_pending_counts_by_slot_ids(
        self, slot_ids: list[int], *, now: datetime | None = None
    ) -> dict[int, tuple[int, int]]:
        """Для каждого slot_id возвращает (confirmed_count, pending_count)."""
        if not slot_ids:
            return {}
        now_utc = now or utc_now()
        counts_q = (
            select(
                Booking.slot_id,
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
            .where(Booking.slot_id.in_(slot_ids))
            .group_by(Booking.slot_id)
        )
        result = await self._session.execute(counts_q)
        return {row.slot_id: (row.confirmed or 0, row.pending or 0) for row in result}
