"""
Pydantic schemas для платежей (Stripe Checkout).
"""
from pydantic import BaseModel, Field, HttpUrl


class CheckoutSessionCreate(BaseModel):
    """Схема для создания Checkout Session."""
    booking_id: int = Field(..., description="ID бронирования для оплаты")
    success_url: HttpUrl = Field(..., description="URL перенаправления после успешной оплаты")
    cancel_url: HttpUrl = Field(..., description="URL перенаправления при отмене")


class CheckoutSessionResponse(BaseModel):
    """Ответ с URL для перехода на Stripe Checkout."""
    checkout_url: str = Field(..., description="URL для redirect на Stripe Checkout")
    session_id: str = Field(..., description="ID Stripe Checkout Session")
