"""Normalize email addresses for case-insensitive identity and booking uniqueness."""

from __future__ import annotations


def normalize_email(value: str) -> str:
    """
    Canonicalize an email for storage and uniqueness checks.

    WHY: PostgreSQL unique indexes on raw guest_email are case-sensitive, while
    ownership checks use lower() — without normalization, Ada@x.com and ada@x.com
    can both hold seats on the same occurrence.
    """
    return value.strip().lower()
