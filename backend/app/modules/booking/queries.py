"""Booking read/query service functions."""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.core.uow import UnitOfWork
from app.models.booking import Booking
from app.models.user import User
from app.modules.booking.policies import is_own_booking
from app.modules.catalog.studio import has_studio_permission


async def get_booking(uow: UnitOfWork, booking_id: int) -> Booking | None:
    """Get booking by ID."""
    return await uow.bookings.get_by_id(booking_id)


async def get_booking_or_raise(uow: UnitOfWork, booking_id: int) -> Booking:
    """Get booking by ID or raise NotFoundError."""
    booking = await uow.bookings.get_by_id(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


async def get_booking_for_user_or_raise(
    uow: UnitOfWork,
    booking_id: int,
    user: User,
) -> Booking:
    """
    Load booking with occurrence+studio; allow own booking or studio owner.

    Returns 404 when the booking does not exist or the user has no access,
    so foreign booking IDs are not enumerable.
    """
    booking = await uow.bookings.get_by_id_with_occurrence_and_studio(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    if not is_own_booking(booking, user) and not await has_studio_permission(
        uow,
        studio=booking.occurrence.studio,
        user=user,
        permission="view_bookings",
    ):
        raise NotFoundError("Booking not found")
    return booking


async def get_owner_bookings(
    uow: UnitOfWork,
    user: User,
    *,
    skip: int = 0,
    limit: int = 20,
    occurrence_id: int | None = None,
    status: str | None = None,
) -> list[Booking]:
    """Studio dashboard: bookings for occurrences visible to this studio member."""
    return await uow.bookings.list_for_studio_member(
        user_id=user.id,
        skip=skip,
        limit=limit,
        occurrence_id=occurrence_id,
        status=status,
    )


async def get_owner_bookings_count(
    uow: UnitOfWork,
    user: User,
    *,
    occurrence_id: int | None = None,
    status: str | None = None,
) -> int:
    """Count bookings for studios visible to this studio member."""
    return await uow.bookings.count_for_studio_member(
        user_id=user.id,
        occurrence_id=occurrence_id,
        status=status,
    )


async def get_bookings(
    uow: UnitOfWork,
    *,
    skip: int = 0,
    limit: int = 20,
    occurrence_id: int | None = None,
    user_id: int | None = None,
    guest_email: str | None = None,
    status: str | None = None,
) -> list[Booking]:
    """
    List bookings with filters.

    occurrence_id — bookings for one occurrence
    user_id — user bookings
    guest_email — guest bookings (before account activation)
    status — pending, confirmed, cancelled, expired, completed
    """
    return await uow.bookings.list_(
        skip=skip,
        limit=limit,
        occurrence_id=occurrence_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )


async def get_bookings_count(
    uow: UnitOfWork,
    *,
    occurrence_id: int | None = None,
    user_id: int | None = None,
    guest_email: str | None = None,
    status: str | None = None,
) -> int:
    """Count bookings for pagination."""
    return await uow.bookings.count(
        occurrence_id=occurrence_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )


async def get_my_bookings(
    uow: UnitOfWork,
    *,
    user: User,
    skip: int = 0,
    limit: int = 50,
    include_guest_email: bool = True,
) -> list[Booking]:
    """
    Bookings list for personal cabinet (occurrence+studio embedded).

    include_guest_email=True merges legacy guest bookings by guest_email == user.email.
    """
    return await uow.bookings.list_my_with_occurrence_and_studio(
        skip=skip,
        limit=limit,
        user_id=user.id,
        user_email=user.email,
        include_guest_email=include_guest_email,
    )


async def attach_guest_bookings(
    uow: UnitOfWork,
    user: User,
    *,
    booking_id: int | None = None,
) -> int:
    """
    Link guest bookings to the authenticated user after OTP verify.

    Matches bookings by guest_email == user.email where user_id is still NULL.
    """
    return await uow.bookings.attach_guest_bookings_by_email(
        user_id=user.id,
        guest_email=user.email,
        booking_id=booking_id,
    )
