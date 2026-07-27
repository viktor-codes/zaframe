"""Stripe Connect onboarding and account status use-cases."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import stripe
import structlog

from app.core.datetime_utils import utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.modules.payment.schemas import validate_checkout_redirect_urls
from app.modules.payment.stripe_client import get_stripe_client, raise_stripe_app_error, run_stripe

logger = structlog.get_logger(__name__)


def _object_value(source: object, key: str) -> object:
    if isinstance(source, dict):
        return cast(dict[str, object], source).get(key)
    return getattr(source, key, None)


def _object_bool(source: object, key: str) -> bool:
    return bool(_object_value(source, key))


def _object_str(source: object, key: str) -> str | None:
    value = _object_value(source, key)
    if value is None:
        return None
    return str(value)


def _datetime_from_unix(value: object) -> datetime | None:
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC)
    return None


def _apply_account_status(studio: Studio, account: object) -> None:
    studio.stripe_charges_enabled = _object_bool(account, "charges_enabled")
    studio.stripe_payouts_enabled = _object_bool(account, "payouts_enabled")
    if studio.stripe_charges_enabled and studio.stripe_payouts_enabled:
        studio.stripe_onboarding_completed_at = studio.stripe_onboarding_completed_at or utc_now()


async def get_stripe_connect_status(uow: UnitOfWork, *, studio_id: int) -> Studio:
    """Return a studio with stored Stripe Connect status."""
    studio = await uow.studios.get_by_id(studio_id)
    if studio is None:
        raise NotFoundError("Studio not found")
    return studio


async def refresh_stripe_connect_status(uow: UnitOfWork, *, studio: Studio) -> Studio:
    """Fetch the Stripe account and refresh stored Connect flags."""
    if not studio.stripe_account_id:
        return studio
    stripe_account_id = studio.stripe_account_id
    client = get_stripe_client()
    try:
        account = await run_stripe(
            lambda: client.v1.accounts.retrieve(account=stripe_account_id)
        )
    except stripe.StripeError as e:
        raise_stripe_app_error(e, action="account status refresh")
    _apply_account_status(studio, account)
    return await uow.studios.save(studio)


async def create_stripe_onboarding_link(
    uow: UnitOfWork,
    *,
    studio: Studio,
    return_url: str,
    refresh_url: str,
) -> tuple[Studio, str]:
    """Create or refresh a Stripe Express onboarding link for a studio."""
    validate_checkout_redirect_urls(return_url, refresh_url)
    client = get_stripe_client()

    if not studio.stripe_account_id:
        try:
            account = await run_stripe(
                lambda: client.v1.accounts.create(
                    params={
                        "type": "express",
                        "capabilities": {
                            "card_payments": {"requested": True},
                            "transfers": {"requested": True},
                        },
                    }
                )
            )
        except stripe.StripeError as e:
            raise_stripe_app_error(e, action="account creation")
        account_id = _object_str(account, "id")
        if not account_id:
            raise ValidationError("Stripe account was not created")
        studio.stripe_account_id = account_id
        _apply_account_status(studio, account)

    stripe_account_id = studio.stripe_account_id
    try:
        link = await run_stripe(
            lambda: client.v1.account_links.create(
                params={
                    "account": stripe_account_id,
                    "refresh_url": refresh_url,
                    "return_url": return_url,
                    "type": "account_onboarding",
                }
            )
        )
    except stripe.StripeError as e:
        raise_stripe_app_error(e, action="account onboarding link creation")
    onboarding_url = _object_str(link, "url")
    if not onboarding_url:
        raise ValidationError("Stripe onboarding link was not created")
    studio.stripe_onboarding_url_expires_at = _datetime_from_unix(_object_value(link, "expires_at"))
    studio = await uow.studios.save(studio)
    log_domain_event(
        logger,
        "stripe_connect_onboarding_started",
        studio_id=studio.id,
        stripe_account_id=studio.stripe_account_id,
    )
    return studio, onboarding_url


async def update_studio_connect_status_from_account(
    uow: UnitOfWork,
    *,
    account: object,
) -> bool:
    """Update studio Connect flags from a Stripe account.updated webhook object."""
    account_id = _object_str(account, "id")
    if account_id is None:
        return False
    studio = await uow.studios.get_by_stripe_account_id(account_id)
    if studio is None:
        return False
    _apply_account_status(studio, account)
    await uow.studios.save(studio)
    log_domain_event(
        logger,
        "stripe_connect_account_updated",
        studio_id=studio.id,
        stripe_account_id=studio.stripe_account_id,
        stripe_charges_enabled=studio.stripe_charges_enabled,
        stripe_payouts_enabled=studio.stripe_payouts_enabled,
    )
    return True
