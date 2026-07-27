"""Search business logic."""

from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.modules.search import SearchResult
from app.modules.search.schemas import SearchServiceResponse, SearchStudioResponse


async def search_studios_and_services(
    uow: UnitOfWork,
    *,
    query: str | None = None,
    category: ServiceCategory | None = None,
    city: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: int | None = 10,
    amenities: list[str] | None = None,
    limit: int = 20,
) -> list[SearchResult]:
    matches = await uow.search.search(
        query=query,
        category=category,
        city=city,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        amenities=amenities,
        limit=limit,
    )
    return [
        SearchResult(
            studio=SearchStudioResponse.model_validate(match.studio),
            matched_services=[
                SearchServiceResponse.model_validate(service) for service in match.matched_services
            ],
        )
        for match in matches
    ]
