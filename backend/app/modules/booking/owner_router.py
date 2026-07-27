"""HTTP: studio booking list and attendance (check-in / no-show)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking import (
    BookingOwnerResponse,
    check_in_booking,
    get_owner_bookings,
    get_owner_bookings_count,
    mark_booking_no_show,
)
from app.modules.booking.mapping import map_owner_booking_with_occurrence
from app.modules.booking.schemas import BookingWithOccurrence
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

owner_router = APIRouter(prefix="/bookings", tags=["bookings"])


@owner_router.get("", response_model=PaginatedResponse[BookingWithOccurrence])
async def list_bookings(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    studio_id: int | None = Query(
        None,
        description="Filter by studio (recommended for dashboard); requires view_bookings",
    ),
    occurrence_id: int | None = Query(None, description="Filter by occurrence"),
    status: str | None = Query(None, description="Filter by status"),
) -> PaginatedResponse[BookingWithOccurrence]:
    """List bookings for studios where the user is a member, with nested occurrence."""
    if studio_id is not None:
        studio = await get_studio_or_raise(uow, studio_id)
        await require_studio_permission(
            uow,
            studio=studio,
            user=user,
            permission="view_bookings",
        )

    skip, limit = pagination_offset(page, size)
    bookings = await get_owner_bookings(
        uow,
        user,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        occurrence_id=occurrence_id,
        status=status,
    )
    total = await get_owner_bookings_count(
        uow,
        user,
        studio_id=studio_id,
        occurrence_id=occurrence_id,
        status=status,
    )
    items = [
        map_owner_booking_with_occurrence(booking)
        for booking in bookings
        if getattr(booking, "occurrence", None) is not None
    ]
    return build_paginated_response(items, total=total, page=page, size=size)


@owner_router.patch("/{booking_id}/check-in", response_model=BookingOwnerResponse)
async def check_in_booking_endpoint(
    booking_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> BookingOwnerResponse:
    """Check in an attendee for an occurrence."""
    booking = await check_in_booking(uow, booking_id=booking_id, user=user)
    return BookingOwnerResponse.model_validate(booking)


@owner_router.patch("/{booking_id}/mark-no-show", response_model=BookingOwnerResponse)
async def mark_booking_no_show_endpoint(
    booking_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> BookingOwnerResponse:
    """Mark an attendee as no-show for an occurrence."""
    booking = await mark_booking_no_show(uow, booking_id=booking_id, user=user)
    return BookingOwnerResponse.model_validate(booking)
