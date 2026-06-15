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
    )
