"""
Stripe Checkout Session param builders.

WHY: Stripe SDK expects SessionCreateParams TypedDicts; building them here
keeps payment service focused on business rules, not API payload shape.
"""

from __future__ import annotations

from stripe.params.checkout import SessionCreateParams
from stripe.params.checkout._session_create_params import (
    SessionCreateParamsLineItem,
    SessionCreateParamsLineItemPriceData,
    SessionCreateParamsLineItemPriceDataProductData,
)


def _build_line_item(
    *,
    currency: str,
    unit_amount_cents: int,
    product_name: str,
    product_description: str,
) -> SessionCreateParamsLineItem:
    product_data: SessionCreateParamsLineItemPriceDataProductData = {
        "name": product_name,
        "description": product_description,
    }
    price_data: SessionCreateParamsLineItemPriceData = {
        "currency": currency,
        "unit_amount": unit_amount_cents,
        "product_data": product_data,
    }
    return {
        "price_data": price_data,
        "quantity": 1,
    }


def _build_payment_checkout_params(
    *,
    success_url: str,
    cancel_url: str,
    currency: str,
    unit_amount_cents: int,
    product_name: str,
    product_description: str,
    metadata: dict[str, str],
    customer_email: str | None,
    expires_at: int | None = None,
    stripe_account_id: str | None = None,
    application_fee_cents: int | None = None,
) -> SessionCreateParams:
    params: SessionCreateParams = {
        "success_url": success_url,
        "cancel_url": cancel_url,
        "mode": "payment",
        "line_items": [
            _build_line_item(
                currency=currency,
                unit_amount_cents=unit_amount_cents,
                product_name=product_name,
                product_description=product_description,
            )
        ],
        "metadata": metadata,
    }
    if customer_email:
        params["customer_email"] = customer_email
    if expires_at is not None:
        params["expires_at"] = expires_at
    if stripe_account_id:
        payment_intent_data: dict[str, object] = {
            "transfer_data": {"destination": stripe_account_id}
        }
        if application_fee_cents is not None and application_fee_cents > 0:
            payment_intent_data["application_fee_amount"] = application_fee_cents
        params["payment_intent_data"] = payment_intent_data  # pyright: ignore[reportGeneralTypeIssues]  # WHY: Stripe SDK TypedDict omits nested Connect fields in this version
    return params


def build_booking_checkout_params(
    *,
    booking_id: int,
    currency: str,
    unit_amount_cents: int,
    product_name: str,
    product_description: str,
    success_url: str,
    cancel_url: str,
    guest_email: str | None,
    expires_at: int | None = None,
    stripe_account_id: str | None = None,
    application_fee_cents: int | None = None,
) -> SessionCreateParams:
    """Build Checkout Session params for a single booking payment."""
    return _build_payment_checkout_params(
        success_url=success_url,
        cancel_url=cancel_url,
        currency=currency,
        unit_amount_cents=unit_amount_cents,
        product_name=product_name,
        product_description=product_description,
        metadata={"booking_id": str(booking_id)},
        customer_email=guest_email,
        expires_at=expires_at,
        stripe_account_id=stripe_account_id,
        application_fee_cents=application_fee_cents,
    )


def build_order_checkout_params(
    *,
    order_id: int,
    currency: str,
    unit_amount_cents: int,
    product_name: str,
    product_description: str,
    success_url: str,
    cancel_url: str,
    guest_email: str | None,
    expires_at: int | None = None,
    stripe_account_id: str | None = None,
    application_fee_cents: int | None = None,
) -> SessionCreateParams:
    """Build Checkout Session params for an order payment."""
    return _build_payment_checkout_params(
        success_url=success_url,
        cancel_url=cancel_url,
        currency=currency,
        unit_amount_cents=unit_amount_cents,
        product_name=product_name,
        product_description=product_description,
        metadata={"order_id": str(order_id)},
        customer_email=guest_email,
        expires_at=expires_at,
        stripe_account_id=stripe_account_id,
        application_fee_cents=application_fee_cents,
    )
