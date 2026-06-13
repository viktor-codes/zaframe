"""Search queries across studios and services."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service, ServiceCategory
from app.models.studio import Studio


@dataclass(frozen=True)
class SearchMatch:
    studio: Studio
    matched_services: list[Service]


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
        radius_km: int | None = 10,
        amenities: list[str] | None = None,
    ) -> list[SearchMatch]:
        conditions = [
            Studio.is_active.is_(True),
            Service.is_active.is_(True),
        ]

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

        studios_stmt = (
            select(Studio)
            .join(Service, Service.studio_id == Studio.id)
            .where(*conditions)
            .distinct(Studio.id)
        )
        if category is not None:
            studios_stmt = studios_stmt.where(text("services.category = :category_filter")).params(
                category_filter=category.value
            )

        studios_result = await self._session.execute(studios_stmt)
        studios: list[Studio] = list(studios_result.scalars().all())
        if not studios:
            return []

        studio_ids = [studio.id for studio in studios]
        service_conditions = [
            Service.studio_id.in_(studio_ids),
            Service.is_active.is_(True),
        ]
        services_stmt = select(Service).where(*service_conditions)
        if category is not None:
            services_stmt = services_stmt.where(text("services.category = :category_filter")).params(
                category_filter=category.value
            )

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
