"""HTTP: list services nested under a studio (dashboard)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.service import (
    ServiceResponse,
    get_services_for_studio,
    get_services_for_studio_count,
)
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

studio_services_router = APIRouter(prefix="/studios", tags=["studios"])


@studio_services_router.get(
    "/{studio_id}/services",
    response_model=PaginatedResponse[ServiceResponse],
)
async def list_studio_services_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    is_active: bool | None = Query(None, description="Filter by service active status"),
) -> PaginatedResponse[ServiceResponse]:
    """List services for a studio dashboard with service-management permission."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_services",
    )
    skip, limit = pagination_offset(page, size)
    services = await get_services_for_studio(
        uow,
        studio_id=studio_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )
    total = await get_services_for_studio_count(
        uow,
        studio_id=studio_id,
        is_active=is_active,
    )
    items = [ServiceResponse.model_validate(service) for service in services]
    return build_paginated_response(items, total=total, page=page, size=size)
