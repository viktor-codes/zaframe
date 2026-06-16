"""
Бизнес-логика для платежей через Stripe.

Почему сервисный слой:
- Создание Checkout Session
- Валидация бронирования перед оплатой
- Изоляция Stripe API от роутеров
"""

from __future__ import annotations

from datetime import datetime

import stripe
import structlog

from app.core.access_tokens import verify_resource_access_token
from app.core.booking_holds import is_active_pending_hold
from app.core.config import settings
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.integrations.stripe.checkout import (
    build_booking_checkout_params,
    build_order_checkout_params,
)
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.modules.booking.policies import is_own_booking
from app.modules.payment.schemas import validate_checkout_redirect_urls

# WHY: paid but occurrence full — studio owner resolves refund/rebook manually (no auto-refund yet).
PAYMENT_STATUS_SUCCEEDED = "succeeded"
PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW = "overbooked_manual_review"

# Stripe Checkout Session minimum lifetime is 30 minutes.
_STRIPE_CHECKOUT_MIN_EXPIRY_SECONDS = 30 * 60

logger = structlog.get_logger(__name__)


def is_own_order(order: Order, user: User) -> bool:
    """True when order belongs to the user (by user_id or guest_email)."""
    if order.user_id is not None and order.user_id == user.id:
        return True
    if order.guest_email is not None:
        return order.guest_email.strip().lower() == user.email.strip().lower()
    return False


def _assert_booking_checkout_access(
    booking: Booking,
    *,
    current_user: User | None,
    access_token: str | None,
) -> None:
    """Allow owner auth or valid guest token; otherwise 404 (no resource enumeration)."""
    if current_user is not None and is_own_booking(booking, current_user):
        return
    if verify_resource_access_token(booking.access_token, access_token):
        return
    raise NotFoundError("Booking not found")


def _assert_order_checkout_access(
    order: Order,
    *,
    current_user: User | None,
    access_token: str | None,
) -> None:
    """Allow owner auth or valid guest token; otherwise 404 (no resource enumeration)."""
    if current_user is not None and is_own_order(order, current_user):
        return
    if verify_resource_access_token(order.access_token, access_token):
        return
    raise NotFoundError("Order not found")


def _get_stripe_client() -> stripe.StripeClient:
    """Получить Stripe-клиент. Выбрасывает AppError при отсутствии ключа."""
    if not settings.STRIPE_SECRET_KEY:
        raise AppError("STRIPE_SECRET_KEY is not configured", status_code=503)
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


def _checkout_session_expires_at(now: datetime) -> int:
    """
    Unix timestamp for Stripe Checkout Session expires_at.

    Aligns with BOOKING_HOLD_MINUTES but respects Stripe's 30-minute minimum.
    """
    hold_seconds = settings.BOOKING_HOLD_MINUTES * 60
    expiry_seconds = max(hold_seconds, _STRIPE_CHECKOUT_MIN_EXPIRY_SECONDS)
    return int(ensure_utc(now).timestamp()) + expiry_seconds


async def _would_exceed_occurrence_capacity(
    uow: UnitOfWork,
    *,
    occurrence: Occurrence,
    booking_id: int,
    now: datetime,
) -> bool:
    """True when confirming booking_id would push the occurrence past max_capacity."""
    confirmed_count = await uow.bookings.count_confirmed_by_occurrence(occurrence.id)
    pending_count = await uow.bookings.count_pending_by_occurrence(
        occurrence.id,
        now=now,
        exclude_booking_id=booking_id,
    )
    return confirmed_count + pending_count + 1 > occurrence.max_capacity


def _booking_counts_as_active_pending_hold(booking: Booking, *, now: datetime) -> bool:
    return is_active_pending_hold(
        status=booking.status,
        reserved_until=booking.reserved_until,
        now=now,
    )


def _would_exceed_occurrence_capacity_in_memory(
    *,
    occurrence: Occurrence,
    booking: Booking,
    capacity_state: dict[int, tuple[int, int]],
    now: datetime,
) -> bool:
    """
    Capacity check using pre-fetched counts plus in-loop confirmations.

    Mirrors per-booking SQL recheck: pending excludes the booking being confirmed;
    capacity_state tracks earlier confirmations in the same order under the same lock.
    """
    confirmed, pending = capacity_state.get(occurrence.id, (0, 0))
    booking_counts_as_pending = _booking_counts_as_active_pending_hold(booking, now=now)
    pending_others = pending - (1 if booking_counts_as_pending else 0)
    return confirmed + pending_others + 1 > occurrence.max_capacity


def _apply_in_memory_confirm_to_capacity_state(
    *,
    occurrence_id: int,
    booking: Booking,
    capacity_state: dict[int, tuple[int, int]],
    now: datetime,
) -> None:
    """Update local counters after confirming a booking (before DB flush)."""
    confirmed, pending = capacity_state.get(occurrence_id, (0, 0))
    if _booking_counts_as_active_pending_hold(booking, now=now):
        pending -= 1
    capacity_state[occurrence_id] = (confirmed + 1, pending)


async def _handle_overbooked_payment(
    uow: UnitOfWork,
    booking: Booking,
    *,
    payment_intent_id: str | None,
) -> None:
    """Mark paid booking for manual studio-owner resolution; do not confirm the seat."""
    now_utc = utc_now()
    booking.status = BookingStatus.CANCELLED
    booking.payment_status = PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    booking.reserved_until = None
    booking.access_token = None
    booking.cancelled_at = now_utc
    if payment_intent_id:
        booking.payment_intent_id = payment_intent_id
    await uow.bookings.flush()
    logger.warning(
        "payment_confirm_overbooked_manual_review",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        payment_intent_id=payment_intent_id,
    )


async def create_checkout_session(
    uow: UnitOfWork,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
    current_user: User | None = None,
    access_token: str | None = None,
) -> dict[str, str]:
    """
    Создать Stripe Checkout Session для оплаты бронирования.

    Authenticated callers must own the booking (user_id or guest_email).
    Guest callers must supply the access_token from booking create response.
    Legacy bookings without a token require authenticated owner access.

    Возвращает: {"checkout_url": "...", "session_id": "..."}
    """
    validate_checkout_redirect_urls(success_url, cancel_url)
    booking = await uow.bookings.get_by_id_with_occurrence(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    _assert_booking_checkout_access(
        booking,
        current_user=current_user,
        access_token=access_token,
    )
    if booking.status != BookingStatus.PENDING:
        raise ValidationError("Booking is already paid or cancelled")
    now_utc = utc_now()
    if not is_active_pending_hold(
        status=booking.status,
        reserved_until=booking.reserved_until,
        now=now_utc,
    ):
        raise ValidationError("Booking hold has expired; please book again")
    if booking.checkout_session_id:
        raise ValidationError("Checkout Session already created for this booking")

    occurrence: Occurrence = booking.occurrence
    if occurrence.price_cents <= 0:
        raise ValidationError("Occurrence has no price for checkout")

    client = _get_stripe_client()
    session = client.v1.checkout.sessions.create(
        params=build_booking_checkout_params(
            booking_id=booking_id,
            currency=settings.STRIPE_CURRENCY,
            unit_amount_cents=occurrence.price_cents,
            product_name=occurrence.title,
            product_description=occurrence.description or f"Booking occurrence #{occurrence.id}",
            success_url=success_url,
            cancel_url=cancel_url,
            guest_email=booking.guest_email,
            expires_at=_checkout_session_expires_at(now_utc),
        )
    )

    booking.checkout_session_id = session.id
    await uow.bookings.flush()

    return {"checkout_url": session.url or "", "session_id": session.id}


async def create_order_checkout_session(
    uow: UnitOfWork,
    order_id: int,
    *,
    success_url: str,
    cancel_url: str,
    current_user: User | None = None,
    access_token: str | None = None,
) -> dict[str, str]:
    """
    Создать Stripe Checkout Session для оплаты заказа (Order).

    Authenticated callers must own the order (user_id or guest_email).
    Guest callers must supply the access_token from course order create response.
    Legacy orders without a token require authenticated owner access.

    Сумма берётся из order.total_amount_cents.
    В metadata сессии обязательно указываем order_id.
    """
    validate_checkout_redirect_urls(success_url, cancel_url)
    order = await uow.orders.get_by_id_with_service(order_id)
    if order is None:
        raise NotFoundError("Order not found")
    _assert_order_checkout_access(
        order,
        current_user=current_user,
        access_token=access_token,
    )
    if order.status != OrderStatus.PENDING:
        raise ValidationError("Order is already paid or cancelled")

    now_utc = utc_now()
    bookings = await uow.bookings.list_(order_id=order_id, limit=1000)
    for booking in bookings:
        if booking.status != BookingStatus.PENDING:
            continue
        if not is_active_pending_hold(
            status=booking.status,
            reserved_until=booking.reserved_until,
            now=now_utc,
        ):
            raise ValidationError("Booking hold has expired; please book again")

    if order.total_amount_cents <= 0:
        raise ValidationError("Order has no payable amount")

    product_name = order.service.name if order.service is not None else f"Заказ #{order.id}"

    client = _get_stripe_client()
    session = client.v1.checkout.sessions.create(
        params=build_order_checkout_params(
            order_id=order_id,
            currency=settings.STRIPE_CURRENCY,
            unit_amount_cents=order.total_amount_cents,
            product_name=product_name,
            product_description=f"Оплата заказа #{order.id}",
            success_url=success_url,
            cancel_url=cancel_url,
            guest_email=order.guest_email,
            expires_at=_checkout_session_expires_at(now_utc),
        )
    )

    await uow.orders.flush()

    return {"checkout_url": session.url or "", "session_id": session.id}


async def confirm_booking_after_payment(
    uow: UnitOfWork,
    booking_id: int,
    *,
    payment_intent_id: str | None = None,
) -> bool:
    """
    Подтвердить бронирование после успешной оплаты (webhook).

    Идемпотентно: если бронирование уже CONFIRMED — ничего не делаем, возвращаем True.
    При overbooking: cancelled + payment_status=overbooked_manual_review (owner resolves).
    Возвращает True если обработано (или уже было), False если бронирование не найдено.
    """
    booking = await uow.bookings.get_by_id(booking_id)
    if booking is None:
        return False
    if booking.status == BookingStatus.CONFIRMED:
        return True
    if (
        booking.status == BookingStatus.CANCELLED
        and booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    ):
        return True

    now_utc = utc_now()
    occurrence = await uow.occurrences.get_by_id_for_update(booking.occurrence_id)
    if occurrence is None:
        return False

    if await _would_exceed_occurrence_capacity(
        uow,
        occurrence=occurrence,
        booking_id=booking.id,
        now=now_utc,
    ):
        await _handle_overbooked_payment(uow, booking, payment_intent_id=payment_intent_id)
        return True

    booking.status = BookingStatus.CONFIRMED
    booking.payment_status = PAYMENT_STATUS_SUCCEEDED
    booking.reserved_until = None
    booking.access_token = None
    if payment_intent_id:
        booking.payment_intent_id = payment_intent_id
    await uow.bookings.flush()
    return True


async def confirm_order_after_payment(
    uow: UnitOfWork,
    order_id: int,
    *,
    payment_intent_id: str | None = None,
) -> bool:
    """
    Подтвердить заказ и все связанные бронирования после успешной оплаты (webhook).

    Идемпотентно: если заказ уже PAID — ничего не делаем, возвращаем True.
    Per-occurrence capacity recheck; overbooked bookings go to manual owner review.
    Возвращает True если обработано (или уже было), False если заказ не найден.
    """
    order = await uow.orders.get_by_id(order_id)
    if order is None:
        return False
    if order.status == OrderStatus.PAID:
        return True

    now_utc = utc_now()
    bookings = await uow.bookings.list_(order_id=order_id, limit=1000)

    occurrence_ids_to_lock = sorted({b.occurrence_id for b in bookings if b.status == BookingStatus.PENDING})
    occurrences_by_id: dict[int, Occurrence] = {}
    # WHY: global lock order to prevent deadlocks (matches occurrence_repo FOR UPDATE order)
    for occurrence_id in occurrence_ids_to_lock:
        occurrence = await uow.occurrences.get_by_id_for_update(occurrence_id)
        if occurrence is not None:
            occurrences_by_id[occurrence_id] = occurrence

    counts_map = await uow.bookings.get_confirmed_pending_counts_by_occurrence_ids(
        occurrence_ids_to_lock,
        now=now_utc,
    )
    capacity_state = {
        occurrence_id: counts_map.get(occurrence_id, (0, 0))
        for occurrence_id in occurrence_ids_to_lock
    }

    order.status = OrderStatus.PAID
    order.access_token = None
    for booking in bookings:
        if booking.status == BookingStatus.CONFIRMED:
            continue
        if (
            booking.status == BookingStatus.CANCELLED
            and booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
        ):
            continue

        occurrence = occurrences_by_id.get(booking.occurrence_id)
        if occurrence is None:
            continue

        if _would_exceed_occurrence_capacity_in_memory(
            occurrence=occurrence,
            booking=booking,
            capacity_state=capacity_state,
            now=now_utc,
        ):
            await _handle_overbooked_payment(uow, booking, payment_intent_id=payment_intent_id)
            continue

        booking.status = BookingStatus.CONFIRMED
        booking.payment_status = PAYMENT_STATUS_SUCCEEDED
        booking.reserved_until = None
        booking.access_token = None
        if payment_intent_id:
            booking.payment_intent_id = payment_intent_id
        _apply_in_memory_confirm_to_capacity_state(
            occurrence_id=occurrence.id,
            booking=booking,
            capacity_state=capacity_state,
            now=now_utc,
        )

    await uow.orders.flush()
    return True
