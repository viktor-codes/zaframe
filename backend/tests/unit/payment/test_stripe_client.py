"""Unit tests for Stripe client async facade and network policy."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import stripe

from app.core.exceptions import ServiceUnavailableError
from app.modules.payment.stripe_client import get_stripe_client, run_stripe


@pytest.mark.asyncio
async def test_run_stripe_executes_operation_off_caller():
    """run_stripe returns the callable result."""
    result = await run_stripe(lambda: 42)
    assert result == 42


@pytest.mark.asyncio
async def test_run_stripe_propagates_stripe_errors():
    """Callers remain responsible for mapping stripe.StripeError."""

    def boom() -> None:
        raise stripe.APIConnectionError("network down")

    with pytest.raises(stripe.APIConnectionError):
        await run_stripe(boom)


def test_get_stripe_client_requires_secret_key():
    with patch("app.modules.payment.stripe_client.settings.STRIPE_SECRET_KEY", None):
        with pytest.raises(ServiceUnavailableError):
            get_stripe_client()


def test_get_stripe_client_applies_timeout_and_retries():
    mock_client = MagicMock()
    with (
        patch("app.modules.payment.stripe_client.settings.STRIPE_SECRET_KEY", "sk_test_x"),
        patch(
            "app.modules.payment.stripe_client.stripe.StripeClient",
            return_value=mock_client,
        ) as mock_cls,
        patch("app.modules.payment.stripe_client.RequestsClient") as mock_http,
    ):
        client = get_stripe_client()

    assert client is mock_client
    mock_http.assert_called_once_with(timeout=15.0)
    _, kwargs = mock_cls.call_args
    assert kwargs["api_key"] == "sk_test_x"
    assert kwargs["max_network_retries"] == 2
    assert kwargs["http_client"] is mock_http.return_value
