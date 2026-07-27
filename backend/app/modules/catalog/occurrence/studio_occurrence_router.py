"""HTTP: occurrences nested under a studio (dashboard schedule)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.occurrence import (
    OccurrenceResponse,
    get_occurrences,
    get_occurrences_count,
)
from app.modules.catalog.occurrence.service import to_occurrence_responses_with_capacity
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

studio_occurrence_router = APIRouter(prefix="/studios", tags=["studios"])


@studio_occurrence_router.get(
    "/{studio_id}/occurrences",
    response_model=PaginatedResponse[OccurrenceResponse],
)
async def list_studio_occurrences(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    start_from: datetime | None = Query(None, description="Date range start"),
    start_to: datetime | None = Query(None, description="Date range end"),
    status: str | None = Query(
        None, description="Filter by status (scheduled/cancelled/completed)"
    ),
) -> PaginatedResponse[OccurrenceResponse]:
    """Studio dashboard schedule: slots with date filters."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="view_dashboard",
    )
    skip, limit = pagination_offset(page, size)
    occurrences = await get_occurrences(
        uow,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    total = await get_occurrences_count(
        uow,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    items = await to_occurrence_responses_with_capacity(uow, occurrences)
    return build_paginated_response(items, total=total, page=page, size=size)
