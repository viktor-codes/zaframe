"""Unit tests for order ownership and guest-token access gate."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.exceptions import NotFoundError
from app.modules.payment.access import assert_order_checkout_access, is_own_order


def _user(*, user_id: int = 1, email: str = "owner@example.com") -> SimpleNamespace:
    return SimpleNamespace(id=user_id, email=email)


def _order(
    *,
    user_id: int | None = None,
    guest_email: str | None = "guest@example.com",
    access_token: str | None = "order-token",
) -> SimpleNamespace:
    return SimpleNamespace(
        user_id=user_id,
        guest_email=guest_email,
        access_token=access_token,
    )


def test_is_own_order_by_user_id():
    assert is_own_order(_order(user_id=1, guest_email=None), _user(user_id=1)) is True


def test_is_own_order_by_guest_email_case_insensitive():
    assert (
        is_own_order(
            _order(user_id=None, guest_email="Ada@Example.com"),
            _user(email="ada@example.com"),
        )
        is True
    )


def test_is_own_order_stranger_denied():
    assert (
        is_own_order(
            _order(user_id=99, guest_email="other@example.com"),
            _user(user_id=1, email="me@example.com"),
        )
        is False
    )


def test_assert_order_checkout_access_token_match():
    assert_order_checkout_access(
        _order(access_token="secret"),
        current_user=None,
        access_token="secret",
    )


def test_assert_order_checkout_access_token_mismatch_raises_not_found():
    with pytest.raises(NotFoundError, match="Order not found"):
        assert_order_checkout_access(
            _order(access_token="secret"),
            current_user=None,
            access_token="wrong",
        )


def test_assert_order_checkout_access_cleared_token_raises_not_found():
    with pytest.raises(NotFoundError, match="Order not found"):
        assert_order_checkout_access(
            _order(access_token=None),
            current_user=None,
            access_token="stale-token",
        )


def test_assert_order_checkout_access_session_owner_without_token():
    assert_order_checkout_access(
        _order(user_id=1, access_token=None),
        current_user=_user(user_id=1),
        access_token=None,
    )
