from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppException,
    BadRequest,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.database.models.order_item import OrderItem
from app.repositories.cart import delete_cart_items_repo, get_cart_items_by_ids_repo
from app.repositories.orders import (
    add_order_items_repo,
    create_order_repo,
    delete_order_repo,
    get_order_by_id_repo,
    get_orders_by_user_id_repo,
    update_order_total_price_repo,
)
from app.repositories.products import update_products_stock_repo
from app.schemas.auth import CurrentUserData
from app.schemas.orders import OrderCreate, OrderListRead, OrderRead


async def get_orders_by_user_id_serv(
    target_user_id: UUID | None, current_user: CurrentUserData, session: AsyncSession
):
    owner_id = target_user_id or current_user.id
    if current_user.role != "admin" and current_user.id != owner_id:
        raise ForbiddenError("You can only view your own orders")
    orders_list = await get_orders_by_user_id_repo(owner_id, session)
    return OrderListRead(
        orders=[OrderRead.model_validate(order) for order in orders_list]
    )


def _validate_product_stock(items_to_check: list[dict]):
    errors = []
    for p_id, data in items_to_check.items():
        if data["available"] < data["requested"]:
            errors.append(
                {
                    "id": str(p_id),
                    "name": data["name"],
                    "requested": data["requested"],
                    "available": data["available"],
                }
            )

    if errors:
        raise BadRequest(message="Insufficient stock", payload=errors)


async def create_order_serv(
    new_order_data: OrderCreate, current_user: CurrentUserData, session: AsyncSession
):
    if len(new_order_data.cart_item_ids) == 0:
        raise ForbiddenError("You must choose cart items")

    owner_id = current_user.id

    cart_items = await get_cart_items_by_ids_repo(
        new_order_data.cart_item_ids, owner_id, session
    )

    if len(cart_items) != len(new_order_data.cart_item_ids):
        raise ForbiddenError("You can only select items from your cart")

    stock_check_map = {
        item.product_id: {
            "name": item.product.name,
            "available": item.product.stock,
            "requested": item.quantity,
        }
        for item in cart_items
    }

    _validate_product_stock(stock_check_map)

    try:
        new_order = await create_order_repo(owner_id, session)

        order_items = []
        total_price = 0
        stock_update_data = []

        for cart_item in cart_items:
            item_sum = cart_item.product.price * cart_item.quantity
            total_price += item_sum

            order_items.append(
                OrderItem(
                    order_id=new_order.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                )
            )
            stock_update_data.append(
                {"product_id": cart_item.product_id, "quantity": -cart_item.quantity}
            )

        await add_order_items_repo(order_items, session)
        await update_order_total_price_repo(new_order.id, total_price, session)
        await delete_cart_items_repo(new_order_data.cart_item_ids, owner_id, session)
        await update_products_stock_repo(stock_update_data, session)

        new_order = await get_order_by_id_repo(new_order.id, owner_id, session)

        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise BadRequest("Order data has changed. Please refresh your cart") from e
    except Exception as e:
        await session.rollback()

        if isinstance(e, AppException):
            raise e

        raise AppException("An unexpected system error occurred") from e
    return OrderRead.model_validate(new_order)


async def delete_order_serv(
    order_id: UUID, current_user: CurrentUserData, session: AsyncSession
):
    owner_id = None if current_user.role == "admin" else current_user.id

    order = await get_order_by_id_repo(order_id, owner_id, session)
    if order is None:
        raise NotFoundError("Order not found or access denied")

    stock_update_data = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in order.items
    ]

    try:
        await update_products_stock_repo(stock_update_data, session)
        success_id = await delete_order_repo(order_id, owner_id, session)

        if not success_id:
            await session.rollback()
            raise ConflictError("Order already deleted")

        await session.commit()
    except Exception as e:
        await session.rollback()

        if isinstance(e, AppException):
            raise e

        raise AppException("An unexpected system error occurred")
