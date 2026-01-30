from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import Settings, get_settings
from app.database.connection.session import get_session
from app.database.models.user import User
from app.schemas.cart import CartItemList, NewCartItemData, UpdateCartItemData
from app.schemas.products import ProductData, ShortProductDataList
from app.services.auth import get_current_user
from app.services.cart import add_product_in_cart, delete_cart, delete_cart_item, get_all_cart_items, update_cart_item_quantity
from app.services.products import get_product_list, get_product_data

app = APIRouter(prefix="/cart", tags=["Cart"])

@app.get("/")
async def get_all_cart_items_handler(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> CartItemList:
    my_cart_items = await get_all_cart_items(current_user, session)
    return my_cart_items

@app.patch("/update_cartitem")
async def update_cart_item_quantity_handler(
    update_cartitem_data: UpdateCartItemData,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await update_cart_item_quantity(update_cartitem_data, session)
    return "Successful update"

@app.post("/create_cartitem/{product_id}")
async def add_product_in_cart_handler(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> NewCartItemData:
    new_cart_item = await add_product_in_cart(product_id, current_user, session)
    return new_cart_item

@app.delete("/delete_cartitem/{cart_item_id}")
async def delete_cart_item_handler(
    cart_item_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await delete_cart_item(cart_item_id, session)
    return "Successful delete"

@app.delete("/delete_my_cart")
async def delete_cart_handler(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await delete_cart(current_user, session)
    return "Successful delete"