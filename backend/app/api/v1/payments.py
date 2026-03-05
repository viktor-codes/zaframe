"""
API роутер для платежей (Stripe Checkout).

Операции:
- POST /payments/checkout-session — создать Checkout Session для бронирования
"""
from fastapi import APIRouter, Depends

from app.api.deps import get_uow
from app.core.uow import UnitOfWork
from app.schemas.payment import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    OrderCheckoutSessionCreate,
)
from app.services.payment import (
    create_checkout_session,
    create_order_checkout_session,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout-session", response_model=CheckoutSessionResponse, status_code=201)
async def create_checkout_session_endpoint(
    schema: CheckoutSessionCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> CheckoutSessionResponse:
    """
    Создать Stripe Checkout Session для оплаты бронирования.

    Возвращает URL для redirect пользователя на страницу оплаты Stripe.
    После успешной оплаты Stripe вызовет webhook и обновит статус бронирования.
    """
    result = await create_checkout_session(
        uow,
        schema.booking_id,
        success_url=str(schema.success_url),
        cancel_url=str(schema.cancel_url),
    )
    return CheckoutSessionResponse(**result)


@router.post(
    "/order-checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=201,
)
async def create_order_checkout_session_endpoint(
    schema: OrderCheckoutSessionCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> CheckoutSessionResponse:
    """
    Создать Stripe Checkout Session для оплаты заказа (Order).

    Сумма берётся из order.total_amount_cents, в metadata сессии попадает order_id.
    """
    result = await create_order_checkout_session(
        uow,
        schema.order_id,
        success_url=str(schema.success_url),
        cancel_url=str(schema.cancel_url),
    )
    return CheckoutSessionResponse(**result)
