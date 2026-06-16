"""Explore list helpers: studios with optional matched services."""

from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.modules.catalog.service import ServiceResponse
from app.modules.catalog.studio import StudioResponse
from app.modules.search import SearchResult


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
    by_studio: dict[int, list[ServiceResponse]] = {}
    for svc in services:
        by_studio.setdefault(svc.studio_id, []).append(ServiceResponse.model_validate(svc))

    return [
        SearchResult(
            studio=StudioResponse.model_validate(s),
            matched_services=by_studio.get(s.id, []),
        )
        for s in studios
    ]
