"""
Бизнес-логика для платежей через Stripe.

Почему сервисный слой:
- Создание Checkout Session
- Валидация бронирования перед оплатой
- Изоляция Stripe API от роутеров
"""

from __future__ import annotations

import stripe

from app.core.booking_holds import is_active_pending_hold
from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.integrations.stripe.checkout import (
    build_booking_checkout_params,
    build_order_checkout_params,
)
from app.models.booking import BookingStatus
from app.models.order import OrderStatus
from app.models.slot import Slot


def _get_stripe_client() -> stripe.StripeClient:
    """Получить Stripe-клиент. Выбрасывает AppError при отсутствии ключа."""
    if not settings.STRIPE_SECRET_KEY:
        raise AppError("STRIPE_SECRET_KEY is not configured", status_code=503)
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


async def create_checkout_session(
    uow: UnitOfWork,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
) -> dict[str, str]:
    """
    Создать Stripe Checkout Session для оплаты бронирования.

    Возвращает: {"checkout_url": "...", "session_id": "..."}
    """
    booking = await uow.bookings.get_by_id_with_slot(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
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

    slot: Slot = booking.slot
    if slot.price_cents <= 0:
        raise ValidationError("Slot has no price for checkout")

    client = _get_stripe_client()
    session = client.v1.checkout.sessions.create(
        params=build_booking_checkout_params(
            booking_id=booking_id,
            currency=settings.STRIPE_CURRENCY,
            unit_amount_cents=slot.price_cents,
            product_name=slot.title,
            product_description=slot.description or f"Бронирование слота #{slot.id}",
            success_url=success_url,
            cancel_url=cancel_url,
            guest_email=booking.guest_email,
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
) -> dict[str, str]:
    """
    Создать Stripe Checkout Session для оплаты заказа (Order).

    Сумма берётся из order.total_amount_cents.
    В metadata сессии обязательно указываем order_id.
    """
    order = await uow.orders.get_by_id_with_service(order_id)
    if order is None:
        raise NotFoundError("Order not found")
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
    Возвращает True если подтверждено (или уже было подтверждено), False если бронирование не найдено.
    """
    booking = await uow.bookings.get_by_id(booking_id)
    if booking is None:
        return False
    if booking.status == BookingStatus.CONFIRMED:
        return True
    booking.status = BookingStatus.CONFIRMED
    booking.payment_status = "succeeded"
    booking.reserved_until = None
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
    Возвращает True если подтверждено (или уже было), False если заказ не найден.
    """
    order = await uow.orders.get_by_id(order_id)
    if order is None:
        return False
    if order.status == OrderStatus.PAID:
        return True
    order.status = OrderStatus.PAID
    bookings = await uow.bookings.list_(order_id=order_id, limit=1000)
    for booking in bookings:
        if booking.status == BookingStatus.CONFIRMED:
            continue
        booking.status = BookingStatus.CONFIRMED
        booking.payment_status = "succeeded"
        booking.reserved_until = None
        if payment_intent_id:
            booking.payment_intent_id = payment_intent_id
    await uow.orders.flush()
    return True
