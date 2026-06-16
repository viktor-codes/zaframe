from typing import Annotated

"""
API router for occurrences (bookable time instances).

CRUD:
- GET /occurrences — list with filters
- GET /occurrences/{id} — single occurrence
- POST /occurrences — create
- PATCH /occurrences/{id} — update
- DELETE /occurrences/{id} — delete

Nested (studio_occurrence_router):
- GET /studios/{studio_id}/occurrences — studio schedule
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.occurrence import (
    OccurrenceCreate,
    OccurrenceResponse,
    OccurrenceUpdate,
    create_occurrence,
    delete_occurrence,
    get_occurrence_or_raise,
    get_occurrences,
    get_occurrences_count,
    update_occurrence,
)
from app.modules.catalog.studio import ensure_studio_owner, get_studio_or_raise

router = APIRouter(prefix="/occurrences", tags=["occurrences"])
studio_occurrence_router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("", response_model=list[OccurrenceResponse])
async def list_occurrences(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Skip N records"),
    limit: int = Query(20, ge=1, le=100, description="Max records"),
    studio_id: int | None = Query(None, description="Filter by studio"),
    start_from: datetime | None = Query(None, description="Range start (UTC)"),
    start_to: datetime | None = Query(None, description="Range end (UTC)"),
    status: str | None = Query(None, description="Filter by status (active/cancelled)"),
) -> list[OccurrenceResponse]:
    """List occurrences with optional studio and date filters."""
    occurrences = await get_occurrences(
        uow,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    return [OccurrenceResponse.model_validate(o) for o in occurrences]


@router.get("/count")
async def count_occurrences(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    studio_id: int | None = Query(None, description="Filter by studio"),
    start_from: datetime | None = Query(None, description="Range start (UTC)"),
    start_to: datetime | None = Query(None, description="Range end (UTC)"),
    status: str | None = Query(None, description="Filter by status (active/cancelled)"),
) -> dict[str, int]:
    """Occurrence count for pagination."""
    count = await get_occurrences_count(
        uow,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    return {"count": count}


@router.get("/{occurrence_id}", response_model=OccurrenceResponse)
async def get_occurrence_by_id(
    occurrence_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OccurrenceResponse:
    """Get occurrence by ID."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    return OccurrenceResponse.model_validate(occurrence)


@router.post("", response_model=OccurrenceResponse, status_code=201)
async def create_occurrence_endpoint(
    schema: OccurrenceCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OccurrenceResponse:
    """Create occurrence (studio owner)."""
    studio = await get_studio_or_raise(uow, schema.studio_id)
    ensure_studio_owner(studio, user.id)
    occurrence = await create_occurrence(uow, schema)
    return OccurrenceResponse.model_validate(occurrence)


@router.patch("/{occurrence_id}", response_model=OccurrenceResponse)
async def update_occurrence_endpoint(
    occurrence_id: int,
    schema: OccurrenceUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OccurrenceResponse:
    """Update occurrence (studio owner)."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    studio = await get_studio_or_raise(uow, occurrence.studio_id)
    ensure_studio_owner(studio, user.id)
    occurrence = await update_occurrence(uow, occurrence, schema)
    return OccurrenceResponse.model_validate(occurrence)


@router.delete("/{occurrence_id}", status_code=204)
async def delete_occurrence_endpoint(
    occurrence_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Delete occurrence (studio owner). Cascades to related bookings."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    studio = await get_studio_or_raise(uow, occurrence.studio_id)
    ensure_studio_owner(studio, user.id)
    await delete_occurrence(uow, occurrence)


@studio_occurrence_router.get("/{studio_id}/occurrences", response_model=list[OccurrenceResponse])
async def list_studio_occurrences(
    studio_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    start_from: datetime | None = Query(None, description="Начало диапазона дат"),
    start_to: datetime | None = Query(None, description="Конец диапазона дат"),
    status: str | None = Query(None, description="Фильтр по статусу (active/cancelled)"),
) -> list[OccurrenceResponse]:
    """Расписание студии: слоты с фильтрами по датам."""
    occurrences = await get_occurrences(
        uow,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        status=status,
    )
    return [OccurrenceResponse.model_validate(o) for o in occurrences]
