"""
API роутер для платежей (Stripe Checkout).

Операции:
- POST /payments/checkout-session — создать Checkout Session для бронирования
"""

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user, get_uow
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.payment.schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    OrderCheckoutSessionCreate,
)
from app.modules.payment.service import (
    create_checkout_session,
    create_order_checkout_session,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout-session", response_model=CheckoutSessionResponse, status_code=201)
@limiter.limit("10/minute")
async def create_checkout_session_endpoint(
    request: Request,
    schema: CheckoutSessionCreate,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User | None = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """
    Создать Stripe Checkout Session для оплаты бронирования.

    Auth optional: guests pay during the active hold window; authenticated users
    may only checkout their own booking (404 on foreign IDs).

    Возвращает URL для redirect пользователя на страницу оплаты Stripe.
    После успешной оплаты Stripe вызовет webhook и обновит статус бронирования.
    """
    result = await create_checkout_session(
        uow,
        schema.booking_id,
        success_url=str(schema.success_url),
        cancel_url=str(schema.cancel_url),
        current_user=current_user,
        access_token=schema.access_token,
    )
    return CheckoutSessionResponse(**result)


@router.post(
    "/order-checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=201,
)
@limiter.limit("10/minute")
async def create_order_checkout_session_endpoint(
    request: Request,
    schema: OrderCheckoutSessionCreate,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User | None = Depends(get_current_user),
) -> CheckoutSessionResponse:
    """
    Создать Stripe Checkout Session для оплаты заказа (Order).

    Auth optional: guests pay during the active hold window; authenticated users
    may only checkout their own order (404 on foreign IDs).

    Сумма берётся из order.total_amount_cents, в metadata сессии попадает order_id.
    """
    result = await create_order_checkout_session(
        uow,
        schema.order_id,
        success_url=str(schema.success_url),
        cancel_url=str(schema.cancel_url),
        current_user=current_user,
        access_token=schema.access_token,
    )
    return CheckoutSessionResponse(**result)
