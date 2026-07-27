"""Search queries across studios and services."""

from __future__ import annotations

import math
from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.service import Service, ServiceCategory, ServiceVisibility
from app.models.studio import Studio
from app.modules.search.schemas import (
    SEARCH_DEFAULT_LIMIT,
    SEARCH_DEFAULT_RADIUS_KM,
    SEARCH_MAX_LIMIT,
    SEARCH_MAX_RADIUS_KM,
    SEARCH_MIN_RADIUS_KM,
)

# Mean Earth radius used by the haversine distance filter (km).
_EARTH_RADIUS_KM = 6371.0


def _clamp_radius_km(radius_km: int | None) -> float:
    if radius_km is None:
        return float(SEARCH_DEFAULT_RADIUS_KM)
    return float(max(SEARCH_MIN_RADIUS_KM, min(radius_km, SEARCH_MAX_RADIUS_KM)))


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return SEARCH_DEFAULT_LIMIT
    return max(1, min(limit, SEARCH_MAX_LIMIT))


@dataclass(frozen=True)
class SearchMatch:
    studio: Studio
    matched_services: list[Service]


def geo_bounding_box_deltas(
    *,
    lat: float,
    radius_km: float,
) -> tuple[float, float]:
    """
    Return (lat_delta_deg, lng_delta_deg) for a crude geo pre-filter.

    Longitude degrees shrink toward the poles; near-polar latitudes use a floor
    so the bbox does not explode.
    """
    lat_delta = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))
    lng_delta = radius_km / (111.0 * max(abs(cos_lat), 0.01))
    return lat_delta, lng_delta


def _haversine_km_expr(*, lat: float, lng: float) -> ColumnElement[float]:
    """SQLAlchemy expression: great-circle distance from (lat, lng) to studio coords."""
    return (
        2
        * _EARTH_RADIUS_KM
        * func.asin(
            func.sqrt(
                func.pow(func.sin(func.radians(Studio.latitude - lat) / 2.0), 2)
                + func.cos(func.radians(lat))
                * func.cos(func.radians(Studio.latitude))
                * func.pow(func.sin(func.radians(Studio.longitude - lng) / 2.0), 2)
            )
        )
    )


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        *,
        query: str | None = None,
        category: ServiceCategory | None = None,
        city: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        radius_km: int | None = SEARCH_DEFAULT_RADIUS_KM,
        amenities: list[str] | None = None,
        limit: int = SEARCH_DEFAULT_LIMIT,
    ) -> list[SearchMatch]:
        conditions: list[ColumnElement[bool]] = [
            Studio.is_active.is_(True),
            Service.is_active.is_(True),
            Service.visibility == ServiceVisibility.PUBLISHED,
        ]
        result_limit = _clamp_limit(limit)

        if city:
            city_normalized = city.strip().lower()
            if city_normalized:
                conditions.append(func.lower(Studio.city) == city_normalized)

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

        if amenities:
            for amenity in amenities:
                amenity_normalized = amenity.strip()
                if amenity_normalized:
                    conditions.append(Studio.amenities.contains([amenity_normalized]))

        if category is not None:
            conditions.append(Service.category == category)

        if lat is not None and lng is not None:
            radius = _clamp_radius_km(radius_km)
            lat_delta, lng_delta = geo_bounding_box_deltas(lat=lat, radius_km=radius)
            conditions.append(
                and_(
                    Studio.latitude.is_not(None),
                    Studio.longitude.is_not(None),
                    func.abs(Studio.latitude - lat) <= lat_delta,
                    func.abs(Studio.longitude - lng) <= lng_delta,
                    _haversine_km_expr(lat=lat, lng=lng) <= radius,
                )
            )

        # WHY: DISTINCT ON (id) requires ORDER BY id first on PostgreSQL.
        studios_stmt = (
            select(Studio)
            .join(Service, Service.studio_id == Studio.id)
            .where(*conditions)
            .distinct(Studio.id)
            .order_by(Studio.id)
            .limit(result_limit)
        )

        studios_result = await self._session.execute(studios_stmt)
        studios: list[Studio] = list(studios_result.scalars().all())
        if not studios:
            return []

        studio_ids = [studio.id for studio in studios]
        service_conditions = [
            Service.studio_id.in_(studio_ids),
            Service.is_active.is_(True),
            Service.visibility == ServiceVisibility.PUBLISHED,
        ]
        if category is not None:
            service_conditions.append(Service.category == category)

        services_stmt = select(Service).where(*service_conditions)
        services_result = await self._session.execute(services_stmt)
        services: list[Service] = list(services_result.scalars().all())

        services_by_studio: dict[int, list[Service]] = {}
        for service in services:
            services_by_studio.setdefault(service.studio_id, []).append(service)

        return [
            SearchMatch(
                studio=studio,
                matched_services=services_by_studio.get(studio.id, []),
            )
            for studio in studios
        ]
