"""HTTP: create single or course booking (optional auth + idempotency)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request

from app.core.deps import get_current_user, get_uow
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking import (
    BookingCreate,
    BookingCreatedResponse,
    create_booking,
    map_booking_created_response,
)
from app.modules.booking.idempotency import (
    fingerprint_booking_create,
    get_active_idempotency_row,
    record_booking_idempotency,
    replay_booking_create_response,
)
from app.modules.booking.order import (
    CourseBookingCreate,
    CourseBookingInput,
    CourseBookingResponse,
    create_course_booking,
)
from app.modules.booking.order.mappers import map_course_booking_result

create_router = APIRouter(prefix="/bookings", tags=["bookings"])


@create_router.post(
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
    idempotency_key: Annotated[
        str | None,
        Header(
            min_length=8,
            max_length=255,
            alias="Idempotency-Key",
            description="Optional client key; retries with the same key return the original hold",
        ),
    ] = None,
) -> BookingCreatedResponse | CourseBookingResponse:
    """
    Create a booking.

    Variants:
    - single occurrence booking (BookingCreate)
    - course purchase (CourseBookingCreate), creating one Order and N bookings

    Auth is optional: with a valid Bearer token, ``user_id`` is set immediately;
    without a token the booking stays guest-owned until OTP attach.

    When ``Idempotency-Key`` is present, repeated creates with the same key and
    payload reuse the original booking/order instead of consuming another seat.
    """
    user_id = user.id if user is not None else None
    fingerprint: str | None = None
    if idempotency_key is not None:
        fingerprint = fingerprint_booking_create(schema, user_id=user_id)
        existing = await get_active_idempotency_row(
            uow,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )
        if existing is not None:
            return await replay_booking_create_response(uow, existing)

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
        if idempotency_key is not None and fingerprint is not None:
            await record_booking_idempotency(
                uow,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                resource_kind="order",
                resource_id=result.order.id,
            )
        return map_course_booking_result(result)
    booking = await create_booking(uow, schema, user=user)  # type: ignore[arg-type]
    if idempotency_key is not None and fingerprint is not None:
        await record_booking_idempotency(
            uow,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_kind="booking",
            resource_id=booking.id,
        )
    return map_booking_created_response(booking)
