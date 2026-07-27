"""HTTP routes for public studio pages (no auth)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_uow
from app.core.uow import UnitOfWork
from app.modules.catalog.occurrence.schemas import OccurrenceResponse
from app.modules.catalog.public import StudioPublicResponse, get_studio_public
from app.modules.catalog.public.mappers import map_studio_public
from app.modules.catalog.public.service import list_public_bookable_occurrences

public_router = APIRouter(prefix="/studios", tags=["studios"])


@public_router.get("/slug/{slug}/public", response_model=StudioPublicResponse)
async def get_studio_public_endpoint(
    slug: str,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioPublicResponse:
    """
    Public studio representation by slug.

    Returns services and upcoming classes.
    """
    return map_studio_public(await get_studio_public(uow, slug=slug))


@public_router.get(
    "/slug/{slug}/services/{service_id}/occurrences",
    response_model=list[OccurrenceResponse],
)
async def list_public_service_occurrences(
    slug: str,
    service_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[OccurrenceResponse]:
    """
    Public bookable occurrence list for a storefront service.

    Includes confirmed/pending seat counts so the booking wizard can disable full slots.
    """
    return await list_public_bookable_occurrences(
        uow,
        slug=slug,
        service_id=service_id,
    )
