"""
Бизнес-логика для платежей через Stripe.

Почему сервисный слой:
- Создание Checkout Session
- Валидация бронирования перед оплатой
- Изоляция Stripe API от роутеров
"""
from __future__ import annotations

import stripe

from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus
from app.models.order import Order, OrderStatus
from app.models.slot import Slot


def _get_stripe_client() -> stripe.StripeClient:
    """Получить Stripe-клиент. Выбрасывает AppError при отсутствии ключа."""
    if not settings.STRIPE_SECRET_KEY:
        raise AppError("STRIPE_SECRET_KEY не настроен", status_code=503)
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
        raise NotFoundError("Бронирование не найдено")
    if booking.status != BookingStatus.PENDING:
        raise ValidationError("Бронирование уже оплачено или отменено")
    if booking.checkout_session_id:
        raise ValidationError("Checkout Session уже создан для этого бронирования")

    slot: Slot = booking.slot
    if slot.price_cents <= 0:
        raise ValidationError("Слот не имеет цены для оплаты")

    client = _get_stripe_client()
    session = client.v1.checkout.sessions.create(
        params={
            "success_url": success_url,
            "cancel_url": cancel_url,
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": settings.STRIPE_CURRENCY,
                        "unit_amount": slot.price_cents,
                        "product_data": {
                            "name": slot.title,
                            "description": (
                                slot.description
                                or f"Бронирование слота #{slot.id}"
                            ),
                        },
                    },
                    "quantity": 1,
                }
            ],
            "metadata": {"booking_id": str(booking_id)},
            "customer_email": booking.guest_email or None,
        }
    )

    booking.checkout_session_id = session.id
    await uow.session.flush()

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
        raise NotFoundError("Заказ не найден")
    if order.status != OrderStatus.PENDING:
        raise ValidationError("Заказ уже оплачен или отменён")

    if order.total_amount_cents <= 0:
        raise ValidationError("Заказ не имеет суммы для оплаты")

    client = _get_stripe_client()

    product_name = (
        order.service.name
        if order.service is not None
        else f"Заказ #{order.id}"
    )

    session = client.v1.checkout.sessions.create(
        params={
            "success_url": success_url,
            "cancel_url": cancel_url,
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": settings.STRIPE_CURRENCY,
                        "unit_amount": order.total_amount_cents,
                        "product_data": {
                            "name": product_name,
                            "description": f"Оплата заказа #{order.id}",
                        },
                    },
                    "quantity": 1,
                }
            ],
            "metadata": {
                "order_id": str(order_id),
            },
            "customer_email": order.guest_email or None,
        }
    )

    await uow.session.flush()

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
    if payment_intent_id:
        booking.payment_intent_id = payment_intent_id
    await uow.session.flush()
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
        if payment_intent_id:
            booking.payment_intent_id = payment_intent_id
    await uow.session.flush()
    return True
