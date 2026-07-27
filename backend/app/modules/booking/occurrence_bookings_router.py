"""HTTP: bookings nested under an occurrence."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking import BookingOwnerResponse, get_bookings, get_bookings_count
from app.modules.catalog.occurrence import get_occurrence_or_raise
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

occurrence_bookings_router = APIRouter(tags=["occurrences"])


@occurrence_bookings_router.get(
    "/occurrences/{occurrence_id}/bookings",
    response_model=PaginatedResponse[BookingOwnerResponse],
)
async def list_occurrence_bookings(
    occurrence_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    status: str | None = Query(None, description="Filter by status"),
) -> PaginatedResponse[BookingOwnerResponse]:
    """Bookings for an occurrence with booking-view permission."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    studio = await get_studio_or_raise(uow, occurrence.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="view_bookings",
    )
    skip, limit = pagination_offset(page, size)
    bookings = await get_bookings(
        uow,
        skip=skip,
        limit=limit,
        occurrence_id=occurrence_id,
        status=status,
    )
    total = await get_bookings_count(
        uow,
        occurrence_id=occurrence_id,
        status=status,
    )
    items = [BookingOwnerResponse.model_validate(booking) for booking in bookings]
    return build_paginated_response(items, total=total, page=page, size=size)
