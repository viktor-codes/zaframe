"""
Studio and service search endpoint.

MVP search with filters by category, city, query, amenities, and geo coordinates.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_uow
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.modules.search import SearchResult
from app.modules.search.service import search_studios_and_services

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search_endpoint(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    query: str | None = Query(None, description="Search query by name/description"),
    category: ServiceCategory | None = Query(None, description="Service category"),
    city: str | None = Query(None, description="City"),
    lat: float | None = Query(None, description="Latitude for geo search"),
    lng: float | None = Query(None, description="Longitude for geo search"),
    radius_km: int | None = Query(10, ge=0, description="Radius in kilometers"),
    amenities: list[str] | None = Query(None, description="Amenities; can be repeated"),
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
    )
