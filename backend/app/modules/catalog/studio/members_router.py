"""HTTP endpoints for studio team member management."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission
from app.modules.catalog.studio.member_schemas import (
    StudioMemberCreate,
    StudioMemberResponse,
    StudioMemberUpdate,
)
from app.modules.catalog.studio.members import (
    add_studio_member,
    count_studio_members,
    list_studio_members,
    remove_studio_member,
    update_studio_member,
)

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get(
    "/{studio_id}/members",
    response_model=PaginatedResponse[StudioMemberResponse],
    summary="List studio members",
)
async def list_studio_members_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
) -> PaginatedResponse[StudioMemberResponse]:
    """List members when the caller has manage_members (owner-only in the matrix)."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_members",
    )
    skip, limit = pagination_offset(page, size)
    items = await list_studio_members(uow, studio_id=studio_id, skip=skip, limit=limit)
    total = await count_studio_members(uow, studio_id=studio_id)
    return build_paginated_response(items, total=total, page=page, size=size)


@router.post(
    "/{studio_id}/members",
    response_model=StudioMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add studio member",
)
async def add_studio_member_endpoint(
    studio_id: int,
    schema: StudioMemberCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioMemberResponse:
    """
    Add an existing user by email as manager or instructor.

    Owner role is only created with the studio. Unknown emails return 404
    (no pending-invite infrastructure in MVP).
    """
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_members",
    )
    return await add_studio_member(uow, studio_id=studio_id, schema=schema)


@router.patch(
    "/{studio_id}/members/{member_id}",
    response_model=StudioMemberResponse,
    summary="Update studio member role",
)
async def update_studio_member_endpoint(
    studio_id: int,
    member_id: int,
    schema: StudioMemberUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioMemberResponse:
    """Change a member to manager or instructor; cannot demote the last owner."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_members",
    )
    return await update_studio_member(
        uow,
        studio_id=studio_id,
        member_id=member_id,
        schema=schema,
    )


@router.delete(
    "/{studio_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove studio member",
)
async def remove_studio_member_endpoint(
    studio_id: int,
    member_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Remove a member; cannot remove the last owner."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_members",
    )
    await remove_studio_member(uow, studio_id=studio_id, member_id=member_id)
