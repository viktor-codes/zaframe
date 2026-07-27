"""HTTP: public/explore studio list (optional auth for owner_id filter)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, get_uow
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.models.user import User
from app.modules.catalog.studio import (
    StudioResponse,
    get_studios,
    get_studios_count,
)
from app.modules.catalog.studio.explore import attach_services_to_studios
from app.modules.search import SearchResult

list_router = APIRouter(prefix="/studios", tags=["studios"])


@list_router.get("")
async def list_studios(
    user: Annotated[User | None, Depends(get_current_user)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    owner_id: int | None = Query(None, description="Filter by owner for owner dashboards"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    city: str | None = Query(None, description="Explore city filter"),
    category: ServiceCategory | None = Query(None, description="Explore service category filter"),
    query: str | None = Query(None, description="Explore studio/service name search"),
    amenities: list[str] | None = Query(None, description="Explore amenities filter"),
    include_services: bool = Query(False, description="Return card services with price/category"),
) -> PaginatedResponse[StudioResponse] | PaginatedResponse[SearchResult]:
    """
    List studios with pagination and optional Explore filters.

    When include_services=true, returns PaginatedResponse[SearchResult];
    otherwise returns PaginatedResponse[StudioResponse].
    """
    if owner_id is not None:
        if user is None:
            raise UnauthorizedError("Authentication required")
        if owner_id != user.id:
            raise ForbiddenError("Access denied for this owner filter")
    skip, limit = pagination_offset(page, size)
    studios = await get_studios(
        uow,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category.value if category is not None else None,
        query=query,
        amenities=amenities,
    )
    total = await get_studios_count(
        uow,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category.value if category is not None else None,
        query=query,
        amenities=amenities,
    )
    if not include_services:
        items = [StudioResponse.model_validate(studio) for studio in studios]
        return build_paginated_response(items, total=total, page=page, size=size)

    search_items = await attach_services_to_studios(
        uow,
        studios,
        category=category.value if category is not None else None,
    )
    return build_paginated_response(search_items, total=total, page=page, size=size)
