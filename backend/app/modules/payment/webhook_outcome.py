"""Durable outcomes for Stripe webhook processing."""

from enum import Enum


class WebhookOutcome(str, Enum):
    """Maps to HTTP ACK policy for Stripe delivery retries.

    PROCESSED / DUPLICATE → HTTP 200 (do not retry).
    RETRY → HTTP 503 (Stripe retries until durable success).
    """

    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    RETRY = "retry"
