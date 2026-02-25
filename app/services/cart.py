from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnprocessableEntityError
from app.database.models.user import User
from app.repositories.cart import (
    delete_cart_from_db,
    delete_cart_item_from_db,
    get_cart_items_from_db,
    insert_cart_item,
    update_cart_item_quantity_in_db,
)
from app.schemas.cart import (
    CartItemData,
    CartItemList,
    NewCartItemData,
    UpdateCartItemData,
)


async def get_all_cart_items(current_user: User, session: AsyncSession):
    cart_items, total_items = await get_cart_items_from_db(current_user, session)
    return CartItemList(
        cart_items=[CartItemData.model_validate(cart_item) for cart_item in cart_items],
        total_items=total_items,
    )


async def add_product_in_cart(
    product_id: UUID, current_user: User, session: AsyncSession
):
    try:
        new_cart_item = await insert_cart_item(product_id, current_user, session)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise ConflictError("Product already in your cart") from e
    return NewCartItemData.model_validate(new_cart_item)


async def update_cart_item_quantity(
    update_cartitem_data: UpdateCartItemData, session: AsyncSession
):
    if update_cartitem_data.new_quantity < 1:
        raise UnprocessableEntityError("New quantity must be greater then 0")
    await update_cart_item_quantity_in_db(update_cartitem_data, session)
    await session.commit()


async def delete_cart_item(cart_item_id: UUID, session: AsyncSession):
    await delete_cart_item_from_db(cart_item_id, session)
    await session.commit()


async def delete_cart(current_user: User, session: AsyncSession):
    await delete_cart_from_db(current_user, session)
    await session.commit()
