"""
Эндпоинт поиска студий и услуг.

MVP‑поиск с фильтрами по категории, городу, запросу, удобствам и гео‑координатам.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_uow
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.modules.search.service import search_studios_and_services
from app.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search_endpoint(
    uow: UnitOfWork = Depends(get_uow),
    query: str | None = Query(None, description="Поисковый запрос по названию/описанию"),
    category: ServiceCategory | None = Query(None, description="Категория услуги"),
    city: str | None = Query(None, description="Город"),
    lat: float | None = Query(None, description="Широта для гео-поиска"),
    lng: float | None = Query(None, description="Долгота для гео-поиска"),
    radius_km: int | None = Query(10, ge=0, description="Радиус в км"),
    amenities: list[str] | None = Query(None, description="Удобства (можно передать несколько)"),
) -> list[SearchResult]:
    """Поиск студий и услуг по комбинированным фильтрам."""
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
