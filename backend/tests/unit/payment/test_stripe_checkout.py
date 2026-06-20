"""
Unit tests for Stripe Checkout Session param builders.

Payload shape is tested here; payment service tests cover validation and orchestration.
"""

from app.integrations.stripe.checkout import (
    build_booking_checkout_params,
    build_order_checkout_params,
)


def test_build_booking_checkout_params_structure():
    params = build_booking_checkout_params(
        booking_id=42,
        currency="eur",
        unit_amount_cents=1500,
        product_name="Morning Class",
        product_description="Occurrence #7",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        guest_email="guest@example.com",
        expires_at=1_700_000_000,
    )

    assert params["mode"] == "payment"
    assert params["success_url"] == "https://example.com/success"
    assert params["cancel_url"] == "https://example.com/cancel"
    assert params["metadata"] == {"booking_id": "42"}
    assert params["customer_email"] == "guest@example.com"
    assert params["expires_at"] == 1_700_000_000

    line_item = params["line_items"][0]
    assert line_item["quantity"] == 1
    assert line_item["price_data"]["currency"] == "eur"
    assert line_item["price_data"]["unit_amount"] == 1500
    assert line_item["price_data"]["product_data"]["name"] == "Morning Class"
    assert line_item["price_data"]["product_data"]["description"] == "Occurrence #7"


def test_build_booking_checkout_params_omits_customer_email_when_none():
    params = build_booking_checkout_params(
        booking_id=1,
        currency="usd",
        unit_amount_cents=1000,
        product_name="Paid",
        product_description="Desc",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        guest_email=None,
    )

    assert "customer_email" not in params


def test_build_order_checkout_params_structure():
    params = build_order_checkout_params(
        order_id=99,
        currency="usd",
        unit_amount_cents=5000,
        product_name="Course Bundle",
        product_description="Оплата заказа #99",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        guest_email="buyer@example.com",
    )

    assert params["metadata"] == {"order_id": "99"}
    assert params["customer_email"] == "buyer@example.com"
    assert params["line_items"][0]["price_data"]["unit_amount"] == 5000
    assert params["line_items"][0]["price_data"]["product_data"]["name"] == "Course Bundle"


def test_build_order_checkout_params_with_connect_destination():
    params = build_order_checkout_params(
        order_id=99,
        currency="eur",
        unit_amount_cents=5000,
        product_name="Course Bundle",
        product_description="Order payment",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        guest_email=None,
        stripe_account_id="acct_123",
        application_fee_cents=250,
    )

    assert params["payment_intent_data"] == {
        "transfer_data": {"destination": "acct_123"},
        "application_fee_amount": 250,
    }
