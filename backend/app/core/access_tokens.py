"""Resource access tokens for guest checkout (IDOR protection)."""

from __future__ import annotations

import secrets


def generate_resource_access_token() -> str:
    """Create an unguessable token for one-time guest resource access."""
    return secrets.token_urlsafe(32)


def verify_resource_access_token(stored: str | None, provided: str | None) -> bool:
    """Constant-time comparison; False when either side is missing."""
    if stored is None or provided is None:
        return False
    return secrets.compare_digest(stored, provided)
