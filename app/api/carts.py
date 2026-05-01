from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_session
from app.schemas.cart import CartItemList, NewCartItemData, UpdateCartItemData
from app.schemas.user import UserTokenData
from app.services.cart import (
    create_cart_item_serv,
    delete_cart_item_serv,
    delete_cart_serv,
    get_cart_items_serv,
    update_cart_item_quantity_serv,
)

app = APIRouter(prefix="/carts", tags=["Carts"])


@app.get("/")
async def get_cart_items_handler(
    target_user_id: UUID | None = None,
    token_data: UserTokenData = Depends(RoleChecker(["user", "admin"])),
    session: AsyncSession = Depends(get_session),
) -> CartItemList:
    my_cart_items = await get_cart_items_serv(target_user_id, token_data, session)
    return my_cart_items


@app.patch("/update_cart_item")
async def update_cart_item_quantity_handler(
    update_cartitem_data: UpdateCartItemData,
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
):
    await update_cart_item_quantity_serv(update_cartitem_data, token_data, session)
    return "Successful update"


@app.post("/create_cart_item/{product_id}")
async def create_cart_item_handler(
    product_id: UUID,
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
) -> NewCartItemData:
    new_cart_item = await create_cart_item_serv(product_id, token_data, session)
    return new_cart_item


@app.delete("/delete_cart_item/{cart_item_id}")
async def delete_cart_item_handler(
    cart_item_id: UUID,
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
):
    await delete_cart_item_serv(cart_item_id, token_data, session)
    return "Successful delete"


@app.delete("/delete_my_cart")
async def delete_cart_handler(
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
):
    await delete_cart_serv(token_data, session)
    return "Successful delete"
