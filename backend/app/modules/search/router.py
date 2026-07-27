"""
Studio and service search endpoint.

MVP search with filters by category, city, query, amenities, and geo coordinates.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.core.deps import get_uow
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.modules.search import SearchResult
from app.modules.search.schemas import (
    SEARCH_DEFAULT_LIMIT,
    SEARCH_DEFAULT_RADIUS_KM,
    SEARCH_MAX_LIMIT,
    SEARCH_MAX_RADIUS_KM,
    SEARCH_MIN_RADIUS_KM,
)
from app.modules.search.service import search_studios_and_services

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
@limiter.limit("60/minute")  # pyright: ignore[reportUnknownMemberType]  # WHY: slowapi ships untyped decorators
async def search_endpoint(
    request: Request,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    query: str | None = Query(None, description="Search query by name/description"),
    category: ServiceCategory | None = Query(None, description="Service category"),
    city: str | None = Query(None, description="City"),
    lat: float | None = Query(None, description="Latitude for geo search"),
    lng: float | None = Query(None, description="Longitude for geo search"),
    radius_km: int | None = Query(
        SEARCH_DEFAULT_RADIUS_KM,
        ge=SEARCH_MIN_RADIUS_KM,
        le=SEARCH_MAX_RADIUS_KM,
        description="Radius in kilometers",
    ),
    amenities: list[str] | None = Query(None, description="Amenities; can be repeated"),
    limit: int = Query(
        SEARCH_DEFAULT_LIMIT,
        ge=1,
        le=SEARCH_MAX_LIMIT,
        description="Max studios to return",
    ),
) -> list[SearchResult]:
    """Search studios and services by combined filters."""
    return await search_studios_and_services(
        uow,
        query=query,
        category=category,
        city=city,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        amenities=amenities,
        limit=limit,
    )
