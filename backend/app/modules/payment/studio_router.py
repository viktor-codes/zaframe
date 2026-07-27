"""Studio-scoped payment API (Stripe Connect, payouts, payment history)."""

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.payment import PaymentStatus
from app.models.studio import Studio
from app.models.user import User
from app.modules.payment.access import require_studio_payout_permission
from app.modules.payment.ledger import count_studio_payments, list_studio_payments
from app.modules.payment.schemas import (
    PaymentListItem,
    PayoutSettingsUpdate,
    StripeConnectOnboardCreate,
    StripeConnectOnboardResponse,
    StripeConnectStatusResponse,
)
from app.modules.payment.service import (
    create_stripe_onboarding_link,
    get_stripe_connect_status,
    refresh_stripe_connect_status,
)

studio_payment_router = APIRouter(prefix="/studios", tags=["payments"])
PaymentStatusFilter = Literal[
    "pending",
    "succeeded",
    "refunded",
    "partially_refunded",
    "failed",
    "manual_review",
]


def _stripe_connect_status_response(studio: Studio) -> StripeConnectStatusResponse:
    return StripeConnectStatusResponse(
        studio_id=studio.id,
        stripe_account_id=studio.stripe_account_id,
        stripe_charges_enabled=studio.stripe_charges_enabled,
        stripe_payouts_enabled=studio.stripe_payouts_enabled,
        stripe_onboarding_completed_at=studio.stripe_onboarding_completed_at,
        stripe_onboarding_url_expires_at=studio.stripe_onboarding_url_expires_at,
    )


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
    response_model=PaginatedResponse[PaymentListItem],
)
async def list_studio_payments_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    status: PaymentStatusFilter | None = Query(
        None,
        description=(
            "Filter by payment status. Allowed values: "
            f"{PaymentStatus.PENDING}, {PaymentStatus.SUCCEEDED}, {PaymentStatus.REFUNDED}, "
            f"{PaymentStatus.PARTIALLY_REFUNDED}, {PaymentStatus.FAILED}, "
            f"{PaymentStatus.MANUAL_REVIEW}"
        ),
    ),
    start_at: datetime | None = Query(None, description="Filter payments created at/after"),
    end_at: datetime | None = Query(None, description="Filter payments created at/before"),
    booking_id: int | None = Query(None, description="Filter by booking ID"),
    order_id: int | None = Query(None, description="Filter by order ID"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
) -> PaginatedResponse[PaymentListItem]:
    """List studio payment history for owner/manager dashboard."""
    studio = await get_stripe_connect_status(uow, studio_id=studio_id)
    await require_studio_payout_permission(
        uow,
        studio=studio,
        user=user,
    )
    skip, limit = pagination_offset(page, size)
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
    total = await count_studio_payments(
        uow,
        studio_id=studio_id,
        status=status,
        start_at=start_at,
        end_at=end_at,
        booking_id=booking_id,
        order_id=order_id,
    )
    items = [PaymentListItem.model_validate(payment) for payment in payments]
    return build_paginated_response(items, total=total, page=page, size=size)
