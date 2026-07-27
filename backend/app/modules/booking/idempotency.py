"""Idempotent POST /bookings helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking_idempotency_key import BookingIdempotencyKey
from app.modules.booking.mapping import map_booking_created_response
from app.modules.booking.order.dto import CourseBookingResultDTO
from app.modules.booking.order.mappers import map_course_booking_result
from app.modules.booking.order.schemas import CourseBookingCreate, CourseBookingResponse
from app.modules.booking.schemas import BookingCreate, BookingCreatedResponse
from app.modules.catalog.service import CourseAvailabilityDTO

ResourceKind = Literal["booking", "order"]

IDEMPOTENCY_KEY_REUSED_MESSAGE = "Idempotency key is already used for a different booking request"


def fingerprint_booking_create(
    schema: BookingCreate | CourseBookingCreate,
    *,
    user_id: int | None,
) -> str:
    """Stable hash of the create payload so key reuse with a different body is rejected."""
    if isinstance(schema, CourseBookingCreate):
        payload: dict[str, object] = {
            "kind": "course",
            "service_id": schema.service_id,
            "guest_email": str(schema.guest_email),
            "guest_name": schema.guest_name,
            "guest_phone": schema.guest_phone,
            "user_id": user_id,
        }
    else:
        payload = {
            "kind": "single",
            "occurrence_id": schema.occurrence_id,
            "guest_email": str(schema.guest_email),
            "guest_name": schema.guest_name,
            "guest_phone": schema.guest_phone,
            "booking_type": schema.booking_type,
            "service_id": schema.service_id,
            "user_id": user_id,
        }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def get_active_idempotency_row(
    uow: UnitOfWork,
    *,
    idempotency_key: str,
    request_fingerprint: str,
) -> BookingIdempotencyKey | None:
    """Return a non-expired ledger row, or None after deleting stale entries."""
    row = await uow.booking_idempotency.get_by_key(idempotency_key)
    if row is None:
        return None
    now = utc_now()
    if ensure_utc(row.expires_at) <= now:
        await uow.booking_idempotency.delete(row)
        return None
    if row.request_fingerprint != request_fingerprint:
        raise ConflictError(IDEMPOTENCY_KEY_REUSED_MESSAGE)
    return row


async def record_booking_idempotency(
    uow: UnitOfWork,
    *,
    idempotency_key: str,
    request_fingerprint: str,
    resource_kind: ResourceKind,
    resource_id: int,
) -> None:
    """Persist ledger row (same transaction as the created booking/order)."""
    await uow.booking_idempotency.add_key(
        idempotency_key=idempotency_key,
        request_fingerprint=request_fingerprint,
        resource_kind=resource_kind,
        resource_id=resource_id,
        expires_at=get_booking_reserved_until(),
    )


async def replay_booking_create_response(
    uow: UnitOfWork,
    row: BookingIdempotencyKey,
) -> BookingCreatedResponse | CourseBookingResponse:
    """Rebuild the create response for a prior successful Idempotency-Key."""
    if row.resource_kind == "booking":
        booking = await uow.bookings.get_by_id(row.resource_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        return map_booking_created_response(booking)

    if row.resource_kind == "order":
        order = await uow.orders.get_by_id_with_bookings(row.resource_id)
        if order is None:
            raise NotFoundError("Order not found")
        if order.access_token is None:
            raise ValidationError("Order access token is missing")
        empty_availability = CourseAvailabilityDTO(
            can_book=True,
            requires_warning=False,
            hard_block=False,
            overbooked_occurrences=[],
            message=None,
        )
        return map_course_booking_result(
            CourseBookingResultDTO(
                order=order,
                bookings=list(order.bookings),
                availability=empty_availability,
            )
        )

    raise ValidationError("Unknown idempotency resource kind")
