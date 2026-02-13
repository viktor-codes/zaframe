from __future__ import annotations

"""
Pydantic-схемы для параметров поиска студий и услуг.
"""

from pydantic import BaseModel, Field

from app.models import ServiceCategory
from app.schemas.service import ServiceResponse
from app.schemas.studio import StudioResponse


class SearchQueryParams(BaseModel):
    """
    Параметры поиска для публичного API.

    Все поля являются опциональными и могут использоваться в различных комбинациях.
    """

    query: str | None = Field(
        None,
        description="Поисковый запрос по названию/описанию",
    )
    category: ServiceCategory | None = Field(
        None,
        description="Категория услуги для фильтрации",
    )
    city: str | None = Field(
        None,
        description="Город для фильтрации студий",
    )
    lat: float | None = Field(
        None,
        description="Широта для гео-поиска",
    )
    lng: float | None = Field(
        None,
        description="Долгота для гео-поиска",
    )
    radius_km: int | None = Field(
        10,
        ge=0,
        description="Радиус поиска в километрах (по умолчанию 10 км)",
    )
    amenities: list[str] | None = Field(
        None,
        description="Список требуемых удобств/опций студии",
    )


class SearchResult(BaseModel):
    """Результат поиска: студия + подходящие услуги."""

    studio: StudioResponse
    matched_services: list[ServiceResponse]

