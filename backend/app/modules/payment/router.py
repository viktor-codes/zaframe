from typing import Annotated

"""
API роутер для платежей (Stripe Checkout).

Операции:
- POST /payments/checkout-session — создать Checkout Session для бронирования
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query, Request

from app.core.deps import get_current_user, get_current_user_required, get_uow
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.models.user import User
from app.modules.payment.access import require_studio_payout_permission
from app.modules.payment.schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    OrderCheckoutSessionCreate,
    PaymentListItem,
    PayoutSettingsUpdate,
    RefundCreate,
    RefundResponse,
    StripeConnectOnboardCreate,
    StripeConnectOnboardResponse,
    StripeConnectStatusResponse,
)
from app.modules.payment.service import (
    create_checkout_session,
    create_order_checkout_session,
    create_refund_for_payment,
    create_stripe_onboarding_link,
    get_payment_or_raise,
    get_payment_studio_or_raise,
    get_stripe_connect_status,
    list_studio_payments,
    refresh_stripe_connect_status,
)

router = APIRouter(prefix="/payments", tags=["payments"])
studio_payment_router = APIRouter(prefix="/studios", tags=["payments"])


def _stripe_connect_status_response(studio: Studio) -> StripeConnectStatusResponse:
    return StripeConnectStatusResponse(
        studio_id=studio.id,
        stripe_account_id=studio.stripe_account_id,
        stripe_charges_enabled=studio.stripe_charges_enabled,
        stripe_payouts_enabled=studio.stripe_payouts_enabled,
        stripe_onboarding_completed_at=studio.stripe_onboarding_completed_at,
        stripe_onboarding_url_expires_at=studio.stripe_onboarding_url_expires_at,
    )


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
        idempotency_key=idempotency_key,
    )
    return CheckoutSessionResponse(**result)


@studio_payment_router.get(
    "/{studio_id}/stripe/status",
    response_model=StripeConnectStatusResponse,
)
async def get_studio_stripe_status_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StripeConnectStatusResponse:
    """Return Stripe Connect status for a studio payout dashboard."""
    studio = await get_stripe_connect_status(uow, studio_id=studio_id)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    return _stripe_connect_status_response(studio)


@studio_payment_router.post(
    "/{studio_id}/stripe/onboard",
    response_model=StripeConnectOnboardResponse,
    status_code=201,
)
async def create_studio_stripe_onboarding_endpoint(
    studio_id: int,
    schema: StripeConnectOnboardCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StripeConnectOnboardResponse:
    """Create a Stripe-hosted Connect onboarding link for a studio."""
    studio = await get_stripe_connect_status(uow, studio_id=studio_id)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    studio, onboarding_url = await create_stripe_onboarding_link(
        uow,
        studio=studio,
        return_url=str(schema.return_url),
        refresh_url=str(schema.refresh_url),
    )
    return StripeConnectOnboardResponse(
        **_stripe_connect_status_response(studio).model_dump(),
        onboarding_url=onboarding_url,
    )


@studio_payment_router.get(
    "/{studio_id}/payout-settings",
    response_model=StripeConnectStatusResponse,
)
async def get_studio_payout_settings_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StripeConnectStatusResponse:
    """Return payout settings for a studio dashboard."""
    studio = await get_stripe_connect_status(uow, studio_id=studio_id)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    return _stripe_connect_status_response(studio)


@studio_payment_router.patch(
    "/{studio_id}/payout-settings",
    response_model=StripeConnectStatusResponse,
)
async def update_studio_payout_settings_endpoint(
    studio_id: int,
    schema: PayoutSettingsUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StripeConnectStatusResponse:
    """Refresh and return payout settings for a studio dashboard."""
    studio = await get_stripe_connect_status(uow, studio_id=studio_id)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    if schema.refresh_from_stripe:
        studio = await refresh_stripe_connect_status(uow, studio=studio)
    return _stripe_connect_status_response(studio)


@studio_payment_router.get(
    "/{studio_id}/payments",
    response_model=list[PaymentListItem],
)
async def list_studio_payments_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    status: str | None = Query(None, description="Filter by payment status"),
    start_at: datetime | None = Query(None, description="Filter payments created at/after"),
    end_at: datetime | None = Query(None, description="Filter payments created at/before"),
    booking_id: int | None = Query(None, description="Filter by booking ID"),
    order_id: int | None = Query(None, description="Filter by order ID"),
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records"),
) -> list[PaymentListItem]:
    """List studio payment history for owner/manager dashboard."""
    studio = await get_stripe_connect_status(uow, studio_id=studio_id)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    payments = await list_studio_payments(
        uow,
        studio_id=studio_id,
        status=status,
        start_at=start_at,
        end_at=end_at,
        booking_id=booking_id,
        order_id=order_id,
        skip=skip,
        limit=limit,
    )
    return [PaymentListItem.model_validate(payment) for payment in payments]


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
