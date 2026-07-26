"""
Payment API router (Stripe Checkout).

Operations:
- POST /payments/checkout-session - create a Checkout Session for a booking
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request

from app.core.deps import get_current_user, get_current_user_required, get_uow
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.payment.access import require_studio_payout_permission
from app.modules.payment.schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    OrderCheckoutSessionCreate,
    RefundCreate,
    RefundResponse,
)
from app.modules.payment.service import (
    create_checkout_session,
    create_order_checkout_session,
    create_refund_for_payment,
    get_payment_or_raise,
    get_payment_studio_or_raise,
)
from app.modules.payment.studio_router import studio_payment_router

router = APIRouter(prefix="/payments", tags=["payments"])

__all__ = ["router", "studio_payment_router"]


@router.post("/checkout-session", response_model=CheckoutSessionResponse, status_code=201)
@limiter.limit("10/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def create_checkout_session_endpoint(
    request: Request,
    schema: CheckoutSessionCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User | None, Depends(get_current_user)],
    idempotency_key: Annotated[
        str | None,
        Header(
            min_length=8,
            max_length=255,
            alias="Idempotency-Key",
            description="Client-generated key for safe checkout retries",
        ),
    ] = None,
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout Session for booking payment.

    Auth optional: guests pay during the active hold window; authenticated users
    may only checkout their own booking (404 on foreign IDs).

    Returns a URL for redirecting the user to Stripe Checkout. After successful
    payment, Stripe calls the webhook and updates the booking status.
    """
    result = await create_checkout_session(
        uow,
        schema.booking_id,
        success_url=str(schema.success_url),
        cancel_url=str(schema.cancel_url),
        current_user=current_user,
        access_token=schema.access_token,
        idempotency_key=idempotency_key,
    )
    return CheckoutSessionResponse(**result)


@router.post(
    "/order-checkout-session",
    response_model=CheckoutSessionResponse,
    status_code=201,
)
@limiter.limit("10/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def create_order_checkout_session_endpoint(
    request: Request,
    schema: OrderCheckoutSessionCreate,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    current_user: Annotated[User | None, Depends(get_current_user)],
    idempotency_key: Annotated[
        str | None,
        Header(
            min_length=8,
            max_length=255,
            alias="Idempotency-Key",
            description="Client-generated key for safe checkout retries",
        ),
    ] = None,
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout Session for order payment.

    Auth optional: guests pay during the active hold window; authenticated users
    may only checkout their own order (404 on foreign IDs).

    The amount comes from order.total_amount_cents; session metadata includes order_id.
    """
    result = await create_order_checkout_session(
        uow,
        schema.order_id,
        success_url=str(schema.success_url),
        cancel_url=str(schema.cancel_url),
        current_user=current_user,
        access_token=schema.access_token,
        idempotency_key=idempotency_key,
    )
    return CheckoutSessionResponse(**result)


@router.post(
    "/{payment_id}/refunds",
    response_model=RefundResponse,
    status_code=201,
)
async def create_payment_refund_endpoint(
    payment_id: int,
    schema: RefundCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    idempotency_key: Annotated[
        str,
        Header(
            min_length=8,
            max_length=255,
            alias="Idempotency-Key",
            description="Client-generated key for safe refund retries",
        ),
    ],
) -> RefundResponse:
    """Create a Stripe refund for a payment after studio payout permission check."""
    payment = await get_payment_or_raise(uow, payment_id=payment_id, for_update=True)
    studio = await get_payment_studio_or_raise(uow, payment=payment)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    refund = await create_refund_for_payment(
        uow,
        payment=payment,
        amount_cents=schema.amount_cents,
        reason=schema.reason,
        idempotency_key=idempotency_key,
    )
    return RefundResponse.model_validate(refund)
