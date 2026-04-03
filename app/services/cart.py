from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, UnprocessableEntityError
from app.repositories.cart import (
    delete_cart_repo,
    delete_cart_item_repo,
    get_cart_items_by_user_id_repo,
    create_cart_item_repo,
    update_cart_item_quantity_repo,
)
from app.schemas.user import UserTokenData
from app.schemas.cart import (
    CartItemData,
    CartItemList,
    NewCartItemData,
    UpdateCartItemData,
)


async def get_cart_items_serv(
    target_user_id: UUID | None, token_data: UserTokenData, session: AsyncSession
):
    owner_id = target_user_id or token_data.id

    if token_data.role != "admin" and token_data.id != owner_id:
        raise ForbiddenError("You can only view your own cart")

    cart_items, total_items = await get_cart_items_by_user_id_repo(owner_id, session)

    return CartItemList(
        cart_items=[CartItemData.model_validate(cart_item) for cart_item in cart_items],
        total_items=total_items,
    )


async def create_cart_item_serv(
    product_id: UUID, token_data: UserTokenData, session: AsyncSession
):
    try:
        new_cart_item = await create_cart_item_repo(product_id, token_data.id, session)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise ConflictError("Product already in your cart") from e

    return NewCartItemData.model_validate(new_cart_item)


async def update_cart_item_quantity_serv(
    update_cart_item_data: UpdateCartItemData,
    token_data: UserTokenData,
    session: AsyncSession,
):
    updated_item_ids = await update_cart_item_quantity_repo(
        update_cart_item_data, token_data.id, session
    )

    if not updated_item_ids:
        raise ForbiddenError("Access denied or item not found")

    await session.commit()


async def delete_cart_item_serv(
    cart_item_id: UUID, token_data: UserTokenData, session: AsyncSession
):
    deleted_item_id = await delete_cart_item_repo(cart_item_id, token_data.id, session)

    if not deleted_item_id:
        raise ForbiddenError("Access denied or item not found")

    await session.commit()


async def delete_cart_serv(token_data: UserTokenData, session: AsyncSession):
    await delete_cart_repo(token_data.id, session)
    await session.commit()
