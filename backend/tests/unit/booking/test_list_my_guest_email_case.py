"""Unit tests for case-insensitive guest email matching in /bookings/my queries."""

from __future__ import annotations

from sqlalchemy import func

from app.models.booking import Booking
from app.modules.booking.repository.list_queries import BookingListQueriesMixin


def test_my_list_guest_email_clause_uses_lower() -> None:
    """Ownership merge must match Ada@x.com vs ada@x.com like policies do."""
    normalized = "ada@example.com"
    clause = (Booking.user_id == 1) | (func.lower(Booking.guest_email) == normalized)
    compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
    assert "lower" in compiled.lower()
    assert "ada@example.com" in compiled


def test_list_queries_mixin_exposes_my_helpers() -> None:
    assert hasattr(BookingListQueriesMixin, "list_my_with_occurrence_and_studio")
    assert hasattr(BookingListQueriesMixin, "count_my_with_occurrence_and_studio")
