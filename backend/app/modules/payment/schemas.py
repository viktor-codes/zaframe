"""
Pydantic schemas для платежей (Stripe Checkout).
"""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl

from app.core.config import settings
from app.core.exceptions import ValidationError


def validate_checkout_redirect_urls(success_url: str, cancel_url: str) -> None:
    """
    Ensure redirect URLs point to an allowed frontend host.

    Raises:
        ValidationError: When either URL host is missing or not in the allowlist.
    """
    allowed = settings.allowed_redirect_hosts
    for url in (success_url, cancel_url):
        host = urlparse(url).hostname
        if host is None or host.lower() not in allowed:
            raise ValidationError("Redirect URL is not allowed")


class CheckoutSessionCreate(BaseModel):
    """
    Схема для создания Checkout Session для одиночного бронирования.

    Used for single-occurrence checkout (Booking).
    """

    booking_id: int = Field(..., description="ID бронирования для оплаты")
    success_url: HttpUrl = Field(
        ...,
        description="URL перенаправления после успешной оплаты",
    )
    cancel_url: HttpUrl = Field(
        ...,
        description="URL перенаправления при отмене",
    )
    access_token: str | None = Field(
        None,
        description="Guest checkout token from booking create response",
    )


class OrderCheckoutSessionCreate(BaseModel):
    """
    Схема для создания Checkout Session для заказа (Order).

    Используется для курсового сценария, когда оплата идёт за весь заказ.
    """

    order_id: int = Field(..., description="ID заказа для оплаты")
    success_url: HttpUrl = Field(
        ...,
        description="URL перенаправления после успешной оплаты",
    )
    cancel_url: HttpUrl = Field(
        ...,
        description="URL перенаправления при отмене",
    )
    access_token: str | None = Field(
        None,
        description="Guest checkout token from course order create response",
    )


class CheckoutSessionResponse(BaseModel):
    """Ответ с URL для перехода на Stripe Checkout."""

    checkout_url: str = Field(
        ...,
        description="URL для redirect на Stripe Checkout",
    )
    session_id: str = Field(
        ...,
        description="ID Stripe Checkout Session",
    )


class StripeConnectStatusResponse(BaseModel):
    """Stripe Connect payout status for a studio dashboard."""

    studio_id: int = Field(..., description="Studio ID")
    stripe_account_id: str | None = Field(None, description="Connected Stripe account ID")
    stripe_charges_enabled: bool = Field(..., description="Whether the account can accept charges")
    stripe_payouts_enabled: bool = Field(..., description="Whether the account can receive payouts")
    stripe_onboarding_completed_at: AwareDatetime | None = Field(
        None,
        description="When both charges and payouts became enabled",
    )
    stripe_onboarding_url_expires_at: AwareDatetime | None = Field(
        None,
        description="Expiration time for the last generated onboarding URL",
    )


class StripeConnectOnboardCreate(BaseModel):
    """Request to create or refresh a Stripe Connect onboarding link."""

    return_url: HttpUrl = Field(..., description="URL Stripe redirects to after onboarding")
    refresh_url: HttpUrl = Field(..., description="URL Stripe redirects to when the link expires")


class StripeConnectOnboardResponse(StripeConnectStatusResponse):
    """Stripe Connect onboarding link response."""

    onboarding_url: str = Field(..., description="Stripe-hosted onboarding URL")


class PayoutSettingsUpdate(BaseModel):
    """Minimal payout settings update contract."""

    refresh_from_stripe: bool = Field(
        True,
        description="When true, refresh the stored Stripe account status before returning settings",
    )


class PaymentListItem(BaseModel):
    """Payment row for owner dashboard history."""

    id: int = Field(..., description="Payment ID")
    booking_id: int | None = Field(None, description="Linked booking ID")
    order_id: int | None = Field(None, description="Linked order ID")
    stripe_checkout_session_id: str = Field(..., description="Stripe Checkout Session ID")
    stripe_payment_intent_id: str | None = Field(None, description="Stripe PaymentIntent ID")
    amount_cents: int = Field(..., description="Payment amount in minor currency units")
    currency: str = Field(..., description="ISO currency code")
    status: str = Field(..., description="Local payment status")
    provider: str = Field(..., description="Payment provider")
    paid_at: AwareDatetime | None = Field(None, description="When payment succeeded")
    refunded_amount_cents: int = Field(..., description="Refunded amount in minor currency units")
    created_at: AwareDatetime = Field(..., description="Ledger creation timestamp")
    updated_at: AwareDatetime = Field(..., description="Ledger update timestamp")

    model_config = ConfigDict(from_attributes=True)


class RefundCreate(BaseModel):
    """Request to refund all or part of a payment."""

    amount_cents: int | None = Field(
        None,
        gt=0,
        description="Refund amount in minor currency units; omitted means remaining amount",
    )
    reason: str | None = Field(
        None,
        max_length=255,
        description="Optional human-readable refund reason",
    )


class RefundResponse(BaseModel):
    """Refund response for owner/admin actions."""

    id: int = Field(..., description="Refund ID")
    payment_id: int = Field(..., description="Payment ID")
    stripe_refund_id: str = Field(..., description="Stripe Refund ID")
    amount_cents: int = Field(..., description="Refund amount in minor currency units")
    reason: str | None = Field(None, description="Refund reason")
    status: str = Field(..., description="Refund status")
    created_at: AwareDatetime = Field(..., description="Refund creation timestamp")

    model_config = ConfigDict(from_attributes=True)
