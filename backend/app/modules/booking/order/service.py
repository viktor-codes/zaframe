"""Course order booking: create Order + N bookings atomically."""

from __future__ import annotations

import structlog

from app.core import datetime_utils
from app.core.access_tokens import generate_resource_access_token
from app.core.booking_holds import get_booking_reserved_until
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models import (
    Booking,
    BookingStatus,
    BookingType,
    Order,
    OrderStatus,
    Service,
)
from app.modules.booking.order.dto import CourseBookingInput, CourseBookingResultDTO
from app.modules.booking.persistence import (
    ensure_no_active_booking_for_guest,
    persist_bookings,
)
from app.modules.catalog.service import check_course_availability_for_update

logger = structlog.get_logger(__name__)


def _calculate_course_order_total_cents(
    service: Service,
    *,
    bookable_occurrence_count: int,
    total_active_occurrence_count: int,
) -> int:
    """
    Course order total for the bookable (active, future) occurrence set.

    When price_course_cents is set, charge proportionally to remaining sessions
    vs all active sessions on the course (mid-term joiners pay a fair share).
    """
    if bookable_occurrence_count <= 0:
        raise ValidationError("Course has no upcoming sessions")

    if service.price_course_cents is not None:
        denominator = total_active_occurrence_count or bookable_occurrence_count
        return round(
            service.price_course_cents * bookable_occurrence_count / denominator,
        )

    return service.price_single_cents * bookable_occurrence_count


def _distribute_course_unit_prices(
    total_amount_cents: int,
    occurrence_count: int,
) -> list[int]:
    """Split order total across occurrences; sum(unit_price_cents) == total_amount_cents."""
    base_unit = total_amount_cents // occurrence_count
    remainder = total_amount_cents % occurrence_count
    return [base_unit + 1] * remainder + [base_unit] * (occurrence_count - remainder)


async def create_course_booking(
    uow: UnitOfWork,
    *,
    data: CourseBookingInput,
) -> CourseBookingResultDTO:
    """
    Create an order and bookings for a course (guest checkout).

    Atomic within the current AsyncSession/transaction.
    """
    now_utc = datetime_utils.utc_now()
    availability = await check_course_availability_for_update(
        uow,
        service_id=data.service_id,
        now=now_utc,
    )
    if not availability.can_book:
        raise ValidationError(
            availability.message or "Not enough seats for the course",
        )

    service = await uow.services.get_by_id(data.service_id)
    if service is None:
        raise NotFoundError("Service not found")
    if not service.is_bookable():
        raise ValidationError("Service is not available for booking")

    occurrences = await uow.occurrences.list_active_future_by_service_for_update(
        data.service_id,
        now=now_utc,
    )
    occurrences = sorted(occurrences, key=lambda o: o.start_time)
    if not occurrences:
        raise ValidationError("Course has no upcoming sessions")

    all_active_occurrences = await uow.occurrences.list_by_service_active(service.id)
    total_amount_cents = _calculate_course_order_total_cents(
        service,
        bookable_occurrence_count=len(occurrences),
        total_active_occurrence_count=len(all_active_occurrences),
    )
    prices = _distribute_course_unit_prices(total_amount_cents, len(occurrences))

    order = await uow.orders.add(
        Order(
            studio_id=service.studio_id,
            service_id=service.id,
            user_id=None,
            guest_email=data.guest_email,
            guest_name=data.guest_name,
            guest_phone=data.guest_phone,
            total_amount_cents=total_amount_cents,
            currency=settings.STRIPE_CURRENCY,
            status=OrderStatus.PENDING,
            access_token=generate_resource_access_token(),
        )
    )

    bookings: list[Booking] = []
    for idx, occurrence in enumerate(occurrences):
        await ensure_no_active_booking_for_guest(
            uow,
            occurrence_id=occurrence.id,
            guest_email=data.guest_email,
        )
        unit_price = prices[idx]
        bookings.append(
            Booking(
                occurrence_id=occurrence.id,
                user_id=None,
                guest_name=data.guest_name,
                guest_email=data.guest_email,
                guest_phone=data.guest_phone,
                status=BookingStatus.PENDING,
                reserved_until=get_booking_reserved_until(now=now_utc),
                booking_type=BookingType.COURSE,
                service_id=service.id,
                order_id=order.id,
                unit_price_cents=unit_price,
            )
        )

    bookings = await persist_bookings(uow, bookings)
    log_domain_event(
        logger,
        "booking_created",
        order_id=order.id,
        service_id=service.id,
        studio_id=service.studio_id,
        booking_count=len(bookings),
        booking_type=BookingType.COURSE,
    )

    return CourseBookingResultDTO(
        order=order,
        bookings=bookings,
        availability=availability,
    )


async def get_my_orders(
    uow: UnitOfWork,
    *,
    user_id: int,
    user_email: str,
    skip: int = 0,
    limit: int = 20,
) -> list[Order]:
    """List orders linked to the current account or matching guest email."""
    return await uow.orders.list_for_user(
        user_id=user_id,
        user_email=user_email,
        skip=skip,
        limit=limit,
    )


async def get_owner_orders(
    uow: UnitOfWork,
    *,
    user_id: int,
    studio_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Order]:
    """List orders for studios visible to the current studio member."""
    return await uow.orders.list_for_studio_member(
        user_id=user_id,
        studio_id=studio_id,
        skip=skip,
        limit=limit,
    )
