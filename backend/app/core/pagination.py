"""Shared pagination envelope for list API responses."""

from pydantic import BaseModel, Field


class PaginatedResponse[T](BaseModel):
    """Uniform list response: items plus paging metadata."""

    items: list[T]
    total: int = Field(ge=0, description="Total matching records across all pages")
    page: int = Field(ge=1, description="Current page number (1-based)")
    size: int = Field(ge=1, le=100, description="Number of records per page")


def pagination_offset(page: int, size: int) -> tuple[int, int]:
    """Convert 1-based page/size to SQL skip/limit."""
    return (page - 1) * size, size


def build_paginated_response[T](
    items: list[T],
    *,
    total: int,
    page: int,
    size: int,
) -> PaginatedResponse[T]:
    """Build a paginated envelope from fetched items and count metadata."""
    return PaginatedResponse(items=items, total=total, page=page, size=size)


def paginate_all[T](items: list[T]) -> PaginatedResponse[T]:
    """Wrap a full in-memory list in a single-page envelope."""
    total = len(items)
    return PaginatedResponse(items=items, total=total, page=1, size=max(total, 1))
