import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError
from app.repositories.cart import (
    create_cart_item_repo,
    delete_cart_item_repo,
    delete_cart_repo,
    get_cart_items_by_user_id_repo,
    update_cart_item_quantity_repo,
)
from app.schemas.cart import (
    CartItemData,
    CartItemList,
    NewCartItemData,
    UpdateCartItemData,
)
from app.schemas.user import UserTokenData

logger = logging.getLogger("service.cart")


async def get_cart_items_serv(
    target_user_id: UUID | None,
    token_data: UserTokenData,
    session: AsyncSession,
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
    product_id: UUID,
    token_data: UserTokenData,
    session: AsyncSession,
):
    try:
        new_cart_item = await create_cart_item_repo(product_id, token_data.id, session)
        await session.commit()

        logger.info(
            "cart_item_create_success",
            extra={
                "product_id": product_id,
                "cart_item_id": new_cart_item.id,
                "cart_id": new_cart_item.cart_id,
            },
        )
        return NewCartItemData.model_validate(new_cart_item)
    except IntegrityError as e:
        await session.rollback()
        raise ConflictError("Product already in your cart") from e
    except Exception:
        await session.rollback()
        raise


async def update_cart_item_quantity_serv(
    update_cart_item_data: UpdateCartItemData,
    token_data: UserTokenData,
    session: AsyncSession,
):
    updated_cart_item = await update_cart_item_quantity_repo(
        update_cart_item_data, token_data.id, session
    )

    if not updated_cart_item:
        raise ForbiddenError("Access denied or item not found")

    await session.commit()

    logger.info(
        "cart_item_quantity_update_success",
        extra={
            "cart_item_id": updated_cart_item.id,
            "cart_id": updated_cart_item.cart_id,
            "new_quantity": updated_cart_item.quantity,
        },
    )


async def delete_cart_item_serv(
    cart_item_id: UUID,
    token_data: UserTokenData,
    session: AsyncSession,
):
    deleted_cart_item = await delete_cart_item_repo(
        cart_item_id, token_data.id, session
    )

    if not deleted_cart_item:
        raise ForbiddenError("Access denied or item not found")

    await session.commit()

    logger.info(
        "cart_item_delete_success",
        extra={
            "cart_item_id": deleted_cart_item.id,
            "cart_id": deleted_cart_item.cart_id,
        },
    )


async def delete_cart_serv(token_data: UserTokenData, session: AsyncSession):
    deleted_cart_id = await delete_cart_repo(token_data.id, session)
    await session.commit()

    logger.info("cart_clear_success", extra={"cart_id": deleted_cart_id})
