from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.exceptions import ValidationError
from app.core.pagination import PaginatedResponse, build_paginated_response, pagination_offset
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking.order.schemas import OrderListItem
from app.modules.booking.order.service import (
    get_my_orders,
    get_my_orders_count,
    get_owner_orders,
    get_owner_orders_count,
)
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/my", response_model=PaginatedResponse[OrderListItem])
async def list_my_orders_endpoint(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
) -> PaginatedResponse[OrderListItem]:
    """List orders for the current customer account."""
    skip, limit = pagination_offset(page, size)
    orders = await get_my_orders(
        uow,
        user_id=user.id,
        user_email=user.email,
        skip=skip,
        limit=limit,
    )
    total = await get_my_orders_count(
        uow,
        user_id=user.id,
        user_email=user.email,
    )
    items = [OrderListItem.model_validate(order) for order in orders]
    return build_paginated_response(items, total=total, page=page, size=size)


@router.get("", response_model=PaginatedResponse[OrderListItem])
async def list_owner_orders_endpoint(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Records per page"),
    studio_id: int | None = Query(None, description="Required studio filter"),
) -> PaginatedResponse[OrderListItem]:
    """List orders for studios owned by the current user."""
    if studio_id is None:
        raise ValidationError("studio_id is required")
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="view_bookings",
    )
    skip, limit = pagination_offset(page, size)
    orders = await get_owner_orders(
        uow,
        user_id=user.id,
        studio_id=studio_id,
        skip=skip,
        limit=limit,
    )
    total = await get_owner_orders_count(
        uow,
        user_id=user.id,
        studio_id=studio_id,
    )
    items = [OrderListItem.model_validate(order) for order in orders]
    return build_paginated_response(items, total=total, page=page, size=size)
