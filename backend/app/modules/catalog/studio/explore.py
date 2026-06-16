"""Explore list helpers: studios with optional matched services."""

from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.modules.search import SearchResult
from app.modules.search.schemas import SearchServiceResponse, SearchStudioResponse


async def attach_services_to_studios(
    uow: UnitOfWork,
    studios: list[Studio],
    *,
    category: str | None,
) -> list[SearchResult]:
    """Map fetched studios to SearchResult with active services for Explore cards."""
    studio_ids = [s.id for s in studios]
    services = await uow.services.list_active_by_studio_ids(
        studio_ids,
        category=category,
    )
    by_studio: dict[int, list[SearchServiceResponse]] = {}
    for svc in services:
        by_studio.setdefault(svc.studio_id, []).append(SearchServiceResponse.model_validate(svc))

    return [
        SearchResult(
            studio=SearchStudioResponse.model_validate(s),
            matched_services=by_studio.get(s.id, []),
        )
        for s in studios
    ]
