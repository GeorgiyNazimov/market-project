from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.database.models.user import User
from app.schemas.cart import UpdateCartItemData


async def get_cart(current_user: User, session: AsyncSession):
    # В большинстве случаев get_cart вызывается для просмотра товаров в
    # корзине или для добавления новых товаров, что означает, что функция завершается
    # после первого быстрого SELECT. INSERT через session.add выполняется
    # редко, и ещё реже — при параллельных запросах срабатывает «страховочный» SELECT.

    cart = (
        await session.execute(select(Cart).where(Cart.user_id == current_user.id))
    ).scalar()
    if not cart:
        cart = Cart(user_id=current_user.id)
        session.add(cart)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            cart = (
                await session.execute(
                    select(Cart).where(Cart.user_id == current_user.id)
                )
            ).scalar_one()
    return cart


async def get_cart_items_from_db(current_user: User, session: AsyncSession):
    cart = await get_cart(current_user, session)
    cart_items = (
        await session.execute(
            select(
                CartItem.quantity.label("quantity"),
                CartItem.product_id,
                CartItem.id,
                Product.name.label("name"),
                Product.price.label("price"),
                (Product.price * CartItem.quantity).label("total_price"),
            )
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == cart.id)
        )
    ).all()
    return cart_items, cart.total_items


async def insert_cart_item(product_id: UUID, current_user: User, session: AsyncSession):
    cart = await get_cart(current_user, session)

    new_cart_item = CartItem(cart_id=cart.id, product_id=product_id)

    await session.execute(
        update(Cart).where(Cart.id == cart.id).values(total_items=Cart.total_items + 1)
    )
    session.add(new_cart_item)
    return new_cart_item


async def update_cart_item_quantity_in_db(
    update_cartitem_data: UpdateCartItemData, session: AsyncSession
):
    result = await session.execute(
        select(CartItem)
        .where(CartItem.id == update_cartitem_data.cart_item_id)
        .with_for_update()
    )
    cart_item = result.scalar_one_or_none()

    delta = update_cartitem_data.new_quantity - cart_item.quantity

    await session.execute(
        update(Cart)
        .where(Cart.id == cart_item.cart_id)
        .values(total_items=Cart.total_items + delta)
    )

    cart_item.quantity = update_cartitem_data.new_quantity


async def delete_cart_item_from_db(cart_item_id: UUID, session: AsyncSession):
    await session.execute(delete(CartItem).where(CartItem.id == cart_item_id))


async def delete_cart_from_db(current_user: User, session: AsyncSession):
    await session.execute(delete(Cart).where(Cart.user_id == current_user.id))
