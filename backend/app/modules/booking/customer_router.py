"""HTTP: customer booking reads and cancel."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking import (
    BookingOwnerResponse,
    BookingSelfListItem,
    BookingSelfResponse,
    cancel_booking,
    get_booking_for_user_or_raise,
    get_my_bookings,
    get_my_bookings_count,
    map_booking_for_user,
)
from app.modules.catalog.occurrence import OccurrenceResponse
from app.modules.catalog.studio import StudioResponse

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/my", response_model=PaginatedResponse[BookingSelfListItem])
async def list_my_bookings(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    include_guest_email: bool = Query(
        True,
        description="Include guest bookings whose guest_email matches the user email",
    ),
) -> PaginatedResponse[BookingSelfListItem]:
    """
    List current-user bookings for the account dashboard without N+1 queries.

    Returns Booking + Occurrence + Studio so the frontend does not need extra requests.
    """
    skip, limit = pagination_offset(page, size)
    bookings = await get_my_bookings(
        uow,
        user=user,
        skip=skip,
        limit=limit,
        include_guest_email=include_guest_email,
    )
    total = await get_my_bookings_count(
        uow,
        user=user,
        include_guest_email=include_guest_email,
    )
    items = [
        BookingSelfListItem(
            **BookingSelfResponse.model_validate(booking).model_dump(),
            occurrence=OccurrenceResponse.model_validate(booking.occurrence),
            studio=StudioResponse.model_validate(booking.occurrence.studio),
        )
        for booking in bookings
        if getattr(booking, "occurrence", None) is not None
        and getattr(booking.occurrence, "studio", None) is not None
    ]
    return build_paginated_response(items, total=total, page=page, size=size)


@router.get("/{booking_id}", response_model=BookingSelfResponse | BookingOwnerResponse)
async def get_booking_by_id(
    booking_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> BookingSelfResponse | BookingOwnerResponse:
    """Fetch a booking by ID when owned by the user or allowed by studio permission."""
    booking = await get_booking_for_user_or_raise(uow, booking_id, user)
    return map_booking_for_user(booking, user)


@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingSelfResponse | BookingOwnerResponse,
)
async def cancel_booking_endpoint(
    booking_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> BookingSelfResponse | BookingOwnerResponse:
    """Cancel own booking, or a studio booking when the user has manage_bookings."""
    booking = await get_booking_for_user_or_raise(uow, booking_id, user)
    cancelled = await cancel_booking(uow, booking, user=user)
    return map_booking_for_user(cancelled, user)
