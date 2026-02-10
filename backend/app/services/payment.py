"""
Бизнес-логика для платежей через Stripe.

Почему сервисный слой:
- Создание Checkout Session
- Валидация бронирования перед оплатой
- Изоляция Stripe API от роутеров
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import stripe

from app.core.config import settings
from app.models.booking import Booking, BookingStatus
from app.models.order import Order, OrderStatus
from app.models.slot import Slot


def _get_stripe_client() -> stripe.StripeClient:
    """Получить Stripe-клиент. Выбрасывает ValueError при отсутствии ключа."""
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY не настроен")
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


async def create_checkout_session(
    db: AsyncSession,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
) -> dict[str, str]:
    """
    Создать Stripe Checkout Session для оплаты бронирования.

    Возвращает: {"checkout_url": "...", "session_id": "..."}
    """
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.slot))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if booking is None:
        raise ValueError("Бронирование не найдено")
    if booking.status != BookingStatus.PENDING:
        raise ValueError("Бронирование уже оплачено или отменено")
    if booking.checkout_session_id:
        raise ValueError("Checkout Session уже создан для этого бронирования")

    slot: Slot = booking.slot
    if slot.price_cents <= 0:
        raise ValueError("Слот не имеет цены для оплаты")

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
                            "description": slot.description or f"Бронирование слота #{slot.id}",
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
    await db.flush()

    return {"checkout_url": session.url or "", "session_id": session.id}


async def create_order_checkout_session(
    db: AsyncSession,
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
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.service))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise ValueError("Заказ не найден")
    if order.status != OrderStatus.PENDING:
        raise ValueError("Заказ уже оплачен или отменён")

    if order.total_amount_cents <= 0:
        raise ValueError("Заказ не имеет суммы для оплаты")

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

    # Для Order мы пока не храним checkout_session_id, достаточно metadata.order_id.
    await db.flush()

    return {"checkout_url": session.url or "", "session_id": session.id}
