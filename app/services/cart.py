from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.repositories.cart import delete_cart_from_db, delete_cart_item_from_db, get_cart_items_from_db, insert_cart_item, update_cart_item_quatity_in_db
from app.repositories.products import create_product, get_product_data_from_db, get_product_list_from_db
from app.schemas.cart import CartItemData, CartItemList, NewCartItemData, UpdateCartItemData
from app.schemas.products import NextCursorData, ProductData, NewProductData, ShortProductData, ShortProductDataList

async def get_all_cart_items(current_user: User, session: AsyncSession):
    cart_items = await get_cart_items_from_db(current_user, session)
    return CartItemList(cart_items=[CartItemData.model_validate(cart_item) for cart_item in cart_items])

async def add_product_in_cart(product_id: UUID, current_user: User, session: AsyncSession):
    new_cart_item = await insert_cart_item(product_id, current_user, session)
    print(new_cart_item)
    return NewCartItemData.model_validate(new_cart_item)

async def update_cart_item_quatity(update_cartitem_data: UpdateCartItemData, session: AsyncSession):
    await update_cart_item_quatity_in_db(update_cartitem_data, session)

async def delete_cart_item(cart_item_id: UUID, session: AsyncSession):
    await delete_cart_item_from_db(cart_item_id, session)

async def delete_cart(current_user: User, session: AsyncSession):
    await delete_cart_from_db(current_user, session)