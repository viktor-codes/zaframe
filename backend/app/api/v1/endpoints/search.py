"""
Эндпоинт поиска студий и услуг.

MVP‑поиск с фильтрами по категории, городу, запросу, удобствам и гео‑координатам.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.service import Service, ServiceCategory
from app.models.studio import Studio
from app.schemas import SearchResult, ServiceResponse, StudioResponse


router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search_endpoint(
    db: AsyncSession = Depends(get_db),
    query: str | None = Query(None, description="Поисковый запрос по названию/описанию"),
    category: ServiceCategory | None = Query(None, description="Категория услуги"),
    city: str | None = Query(None, description="Город"),
    lat: float | None = Query(None, description="Широта для гео-поиска"),
    lng: float | None = Query(None, description="Долгота для гео-поиска"),
    radius_km: int | None = Query(10, ge=0, description="Радиус в км"),
    amenities: list[str] | None = Query(None, description="Удобства (можно передать несколько)"),
) -> list[SearchResult]:
    """
    Поиск студий и услуг по комбинированным фильтрам.

    Базовый запрос строится от Studio с join на Service и distinct по студии,
    чтобы одна студия не дублировалась в выдаче.
    """
    conditions = [
        Studio.is_active.is_(True),
        Service.is_active.is_(True),
    ]

    # Фильтр по городу (регистронезависимый)
    if city:
        city_normalized = city.strip().lower()
        if city_normalized:
            conditions.append(func.lower(Studio.city) == city_normalized)

    # Поисковый запрос по названию услуги или студии
    if query:
        query_normalized = query.strip()
        if query_normalized:
            pattern = f"%{query_normalized}%"
            conditions.append(
                or_(
                    Service.name.ilike(pattern),
                    Studio.name.ilike(pattern),
                )
            )

    # Фильтр по удобствам (JSON‑массив, должен содержать все указанные элементы)
    if amenities:
        for amenity in amenities:
            amenity_normalized = amenity.strip()
            if amenity_normalized:
                conditions.append(Studio.amenities.contains([amenity_normalized]))

    # Простейший гео‑поиск по окну вокруг точки (lat/lng)
    if lat is not None and lng is not None:
        radius = radius_km or 10
        delta_deg = radius / 111.0
        conditions.append(
            and_(
                Studio.latitude.is_not(None),
                Studio.longitude.is_not(None),
                func.abs(Studio.latitude - lat) <= delta_deg,
                func.abs(Studio.longitude - lng) <= delta_deg,
            )
        )

    # Базовый запрос: получаем уникальные студии, удовлетворяющие условиям
    studios_stmt = (
        select(Studio)
        .join(Service, Service.studio_id == Studio.id)
        .where(*conditions)
        .distinct(Studio.id)
    )
    # Фильтр по категории: сравниваем с raw value enum ('yoga', 'boxing', ...)
    if category is not None:
        studios_stmt = studios_stmt.where(
            text("services.category = :category_filter")
        ).params(category_filter=category.value)
    studios_result = await db.execute(studios_stmt)
    studios: list[Studio] = list(studios_result.scalars().all())

    if not studios:
        return []

    studio_ids = [s.id for s in studios]

    # Для matched_services:
    # - если указана category: берём только услуги этой категории
    # - если category не указана: берём все активные услуги студии
    service_conditions = [
        Service.studio_id.in_(studio_ids),
        Service.is_active.is_(True),
    ]

    services_stmt = select(Service).where(*service_conditions)
    if category is not None:
        services_stmt = services_stmt.where(
            text("services.category = :category_filter")
        ).params(category_filter=category.value)
    services_result = await db.execute(services_stmt)
    services: list[Service] = list(services_result.scalars().all())

    services_by_studio: dict[int, list[Service]] = {}
    for service in services:
        services_by_studio.setdefault(service.studio_id, []).append(service)

    results: list[SearchResult] = []
    for studio in studios:
        matched_services = services_by_studio.get(studio.id, [])

        results.append(
            SearchResult(
                studio=StudioResponse.model_validate(studio),
                matched_services=[
                    ServiceResponse.model_validate(s) for s in matched_services
                ],
            )
        )

    return results

