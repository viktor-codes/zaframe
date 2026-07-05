"""Unit tests for pagination helpers."""

from app.core.pagination import build_paginated_response, paginate_all, pagination_offset


def test_pagination_offset_converts_page_and_size() -> None:
    assert pagination_offset(1, 20) == (0, 20)
    assert pagination_offset(3, 10) == (20, 10)


def test_build_paginated_response_wraps_items_and_metadata() -> None:
    payload = build_paginated_response(["a", "b"], total=12, page=2, size=2)

    assert payload.items == ["a", "b"]
    assert payload.total == 12
    assert payload.page == 2
    assert payload.size == 2


def test_paginate_all_returns_single_page_for_full_list() -> None:
    payload = paginate_all([1, 2, 3])

    assert payload.items == [1, 2, 3]
    assert payload.total == 3
    assert payload.page == 1
    assert payload.size == 3


def test_paginate_all_handles_empty_list() -> None:
    payload = paginate_all([])

    assert payload.items == []
    assert payload.total == 0
    assert payload.page == 1
    assert payload.size == 1
