from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, RoleChecker
from app.schemas.auth import CurrentUserData
from app.schemas.orders import OrderCreate, OrderListRead, OrderRead
from app.services.orders import (
    get_orders_by_user_id_serv,
    delete_order_serv,
    create_order_serv,
)

app = APIRouter(prefix="/order", tags=["Order"])


@app.get("/")
async def get_current_orders_handler(
    target_user_id: UUID | None = None,
    current_user: CurrentUserData = Depends(RoleChecker(["user", "admin"])),
    session: AsyncSession = Depends(get_session),
) -> OrderListRead:
    orders = await get_orders_by_user_id_serv(target_user_id, current_user, session)
    return orders


@app.post("/create_order")
async def create_order_handler(
    new_order_data: OrderCreate,
    current_user: CurrentUserData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
) -> OrderRead:
    new_order = await create_order_serv(new_order_data, current_user, session)
    return new_order


@app.delete("/delete_order/{order_id}")
async def delete_order_handler(
    order_id: UUID,
    current_user: CurrentUserData = Depends(RoleChecker(["user", "admin"])),
    session: AsyncSession = Depends(get_session),
):
    await delete_order_serv(order_id, current_user, session)
    return "Successful delete"
