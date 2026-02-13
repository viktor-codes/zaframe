"""
Эндпоинт поиска студий и услуг.

MVP‑поиск с фильтрами по категории, городу, запросу, удобствам и гео‑координатам.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.service import Service
from app.models.studio import Studio
from app.schemas import SearchQueryParams, SearchResult, ServiceResponse, StudioResponse


router = APIRouter(prefix="/search", tags=["search"])

SearchParams = Annotated[SearchQueryParams, Depends()]


@router.get("", response_model=list[SearchResult])
async def search_endpoint(
    params: SearchParams,
    db: AsyncSession = Depends(get_db),
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

    # Фильтр по категории услуги
    if params.category is not None:
        conditions.append(Service.category == params.category)

    # Фильтр по городу (регистронезависимый)
    if params.city:
        city_normalized = params.city.strip().lower()
        if city_normalized:
            conditions.append(func.lower(Studio.city) == city_normalized)

    # Поисковый запрос по названию услуги или студии
    if params.query:
        query_normalized = params.query.strip()
        if query_normalized:
            pattern = f"%{query_normalized}%"
            conditions.append(
                or_(
                    Service.name.ilike(pattern),
                    Studio.name.ilike(pattern),
                )
            )

    # Фильтр по удобствам (JSON‑массив, должен содержать все указанные элементы)
    if params.amenities:
        for amenity in params.amenities:
            amenity_normalized = amenity.strip()
            if amenity_normalized:
                conditions.append(Studio.amenities.contains([amenity_normalized]))

    # Простейший гео‑поиск по окну вокруг точки (lat/lng)
    if params.lat is not None and params.lng is not None:
        radius_km = params.radius_km or 10
        # Примерное преобразование километров в градусы (1° ≈ 111 км)
        delta_deg = radius_km / 111.0
        conditions.append(
            and_(
                Studio.latitude.is_not(None),
                Studio.longitude.is_not(None),
                func.abs(Studio.latitude - params.lat) <= delta_deg,
                func.abs(Studio.longitude - params.lng) <= delta_deg,
            )
        )

    # Базовый запрос: получаем уникальные студии, удовлетворяющие условиям
    studios_stmt = (
        select(Studio)
        .join(Service, Service.studio_id == Studio.id)
        .where(*conditions)
        .distinct(Studio.id)
    )
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
    if params.category is not None:
        service_conditions.append(Service.category == params.category)

    services_stmt = select(Service).where(*service_conditions)
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

