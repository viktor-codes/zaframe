"""Helpers for paginated API responses in integration tests."""


def paginated_items(payload: dict | list) -> list:
    """Extract list items from the `{items, total, page, size}` envelope."""
    if isinstance(payload, dict):
        return payload["items"]
    return payload
