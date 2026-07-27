"""
Booking API router.

Operations:
- POST /bookings - create a booking in guest mode
- GET /bookings - list bookings with filters
- GET /bookings/{id} - fetch one booking
- PATCH /bookings/{id}/cancel - cancel a booking
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_current_user, get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking import (
    BookingCreate,
    BookingCreatedResponse,
    BookingOwnerResponse,
    BookingSelfListItem,
    BookingSelfResponse,
    cancel_booking,
    check_in_booking,
    create_booking,
    get_booking_for_user_or_raise,
    get_bookings,
    get_bookings_count,
    get_my_bookings,
    get_my_bookings_count,
    get_owner_bookings,
    get_owner_bookings_count,
    map_booking_created_response,
    map_booking_for_user,
    mark_booking_no_show,
)
from app.modules.booking.mapping import map_owner_booking_with_occurrence
from app.modules.booking.order import (
    CourseBookingCreate,
    CourseBookingInput,
    CourseBookingResponse,
    create_course_booking,
)
from app.modules.booking.order.mappers import map_course_booking_result
from app.modules.booking.schemas import BookingWithOccurrence
from app.modules.catalog.occurrence import OccurrenceResponse, get_occurrence_or_raise
from app.modules.catalog.studio import (
    StudioResponse,
    get_studio_or_raise,
    require_studio_permission,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])
occurrence_bookings_router = APIRouter(tags=["occurrences"])


@router.post(
    "",
    response_model=BookingCreatedResponse | CourseBookingResponse,
    status_code=201,
)
@limiter.limit("10/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def create_booking_endpoint(
    request: Request,
    schema: BookingCreate | CourseBookingCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User | None, Depends(get_current_user)],
) -> BookingCreatedResponse | CourseBookingResponse:
    """
    Create a booking.

    Variants:
    - single occurrence booking (BookingCreate)
    - course purchase (CourseBookingCreate), creating one Order and N bookings

    Auth is optional: with a valid Bearer token, ``user_id`` is set immediately;
    without a token the booking stays guest-owned until OTP attach.
    """
    if isinstance(schema, CourseBookingCreate):
        result = await create_course_booking(
            uow,
            data=CourseBookingInput(
                service_id=schema.service_id,
                guest_name=schema.guest_name,
                guest_email=schema.guest_email,
                guest_phone=schema.guest_phone,
            ),
            user=user,
        )
        return map_course_booking_result(result)
    booking = await create_booking(uow, schema, user=user)  # type: ignore[arg-type]
    return map_booking_created_response(booking)


@router.get("", response_model=PaginatedResponse[BookingWithOccurrence])
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


@router.patch("/{booking_id}/check-in", response_model=BookingOwnerResponse)
async def check_in_booking_endpoint(
    booking_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> BookingOwnerResponse:
    """Check in an attendee for an occurrence."""
    booking = await check_in_booking(uow, booking_id=booking_id, user=user)
    return BookingOwnerResponse.model_validate(booking)


@router.patch("/{booking_id}/mark-no-show", response_model=BookingOwnerResponse)
async def mark_booking_no_show_endpoint(
    booking_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    user: Annotated[User, Depends(get_current_user_required)],
) -> BookingOwnerResponse:
    """Mark an attendee as no-show for an occurrence."""
    booking = await mark_booking_no_show(uow, booking_id=booking_id, user=user)
    return BookingOwnerResponse.model_validate(booking)


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
