from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking.order.schemas import OrderListItem
from app.modules.booking.order.service import get_my_orders, get_owner_orders
from app.modules.catalog.studio import ensure_studio_owner, get_studio_or_raise

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/my", response_model=list[OrderListItem])
async def list_my_orders_endpoint(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
) -> list[OrderListItem]:
    """List orders for the current customer account."""
    orders = await get_my_orders(
        uow,
        user_id=user.id,
        user_email=user.email,
        skip=skip,
        limit=limit,
    )
    return [OrderListItem.model_validate(order) for order in orders]


@router.get("", response_model=list[OrderListItem])
async def list_owner_orders_endpoint(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    studio_id: int | None = Query(None, description="Optional owned studio filter"),
) -> list[OrderListItem]:
    """List orders for studios owned by the current user."""
    if studio_id is not None:
        studio = await get_studio_or_raise(uow, studio_id)
        ensure_studio_owner(studio, user.id)
    orders = await get_owner_orders(
        uow,
        owner_id=user.id,
        studio_id=studio_id,
        skip=skip,
        limit=limit,
    )
    return [OrderListItem.model_validate(order) for order in orders]
