"""
Pydantic schemas для платежей (Stripe Checkout).
"""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl

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
