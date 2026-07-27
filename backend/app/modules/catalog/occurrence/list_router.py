"""HTTP: occurrence list endpoints for studio dashboard and instructors."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.exceptions import ValidationError
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.occurrence import (
    OccurrenceResponse,
    get_my_instructor_occurrences,
    get_occurrences,
    get_occurrences_count,
)
from app.modules.catalog.occurrence.service import get_my_instructor_occurrences_count
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

list_router = APIRouter(prefix="/occurrences", tags=["occurrences"])


@list_router.get("", response_model=PaginatedResponse[OccurrenceResponse])
async def list_occurrences(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    studio_id: int | None = Query(None, description="Filter by studio"),
    instructor_id: int | None = Query(None, description="Filter by assigned studio member"),
    start_from: datetime | None = Query(None, description="Range start (UTC)"),
    start_to: datetime | None = Query(None, description="Range end (UTC)"),
    status: str | None = Query(
        None, description="Filter by status (scheduled/cancelled/completed)"
    ),
) -> PaginatedResponse[OccurrenceResponse]:
    """List studio occurrences for an authenticated studio dashboard."""
    if studio_id is None:
        raise ValidationError("studio_id is required")
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
        instructor_id=instructor_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    total = await get_occurrences_count(
        uow,
        studio_id=studio_id,
        instructor_id=instructor_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    items = [OccurrenceResponse.model_validate(occurrence) for occurrence in occurrences]
    return build_paginated_response(items, total=total, page=page, size=size)


@list_router.get("/mine", response_model=PaginatedResponse[OccurrenceResponse])
async def list_my_instructor_occurrences(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    studio_id: int | None = Query(None, description="Filter by studio"),
    start_from: datetime | None = Query(None, description="Range start (UTC)"),
    start_to: datetime | None = Query(None, description="Range end (UTC)"),
    status: str | None = Query(
        None, description="Filter by status (scheduled/cancelled/completed)"
    ),
) -> PaginatedResponse[OccurrenceResponse]:
    """List occurrences assigned to the current instructor."""
    skip, limit = pagination_offset(page, size)
    occurrences = await get_my_instructor_occurrences(
        uow,
        user_id=user.id,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    total = await get_my_instructor_occurrences_count(
        uow,
        user_id=user.id,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    items = [OccurrenceResponse.model_validate(occurrence) for occurrence in occurrences]
    return build_paginated_response(items, total=total, page=page, size=size)
