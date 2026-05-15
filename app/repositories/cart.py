from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.schemas.cart import UpdateCartItemData


async def create_cart_item_repo(product_id: UUID, user_id: UUID, session: AsyncSession):
    cart = await get_cart_repo(user_id, session)
    new_cart_item = CartItem(cart_id=cart.id, product_id=product_id)
    session.add(new_cart_item)
    return new_cart_item


async def get_cart_repo(user_id: UUID, session: AsyncSession):
    # В большинстве случаев get_cart вызывается для просмотра товаров в
    # корзине или для добавления новых товаров, что означает, что функция завершается
    # после первого быстрого SELECT. INSERT через session.add выполняется
    # редко, и ещё реже — при параллельных запросах срабатывает «страховочный» SELECT.

    stmt = select(Cart).where(Cart.user_id == user_id)
    cart = (await session.execute(stmt)).scalar()
    if cart:
        return cart

    try:
        async with session.begin_nested():
            cart = Cart(user_id=user_id)
            session.add(cart)
            await session.flush()
        return cart
    except IntegrityError:
        return (await session.execute(stmt)).scalar_one()


async def get_cart_items_by_user_id_repo(user_id: UUID, session: AsyncSession):
    cart_items = (
        await session.execute(
            select(
                CartItem.id,
                CartItem.product_id,
                Product.name,
                Product.price,
                CartItem.quantity,
                (Product.price * CartItem.quantity).label("total_price"),
                func.sum(CartItem.quantity).over().label("total_items"),
            )
            .select_from(Cart)
            .join(Cart.items)
            .join(CartItem.product)
            .where(Cart.user_id == user_id)
        )
    ).all()

    if not cart_items:
        return [], 0

    total_items = cart_items[0].total_items
    return cart_items, total_items


async def get_cart_items_by_ids_repo(
    cart_item_ids: list[UUID], user_id: UUID | None, session: AsyncSession
):
    stmt = (
        select(CartItem)
        .join(CartItem.cart)
        .options(
            selectinload(CartItem.product),
            contains_eager(CartItem.cart).joinedload(Cart.user),
        )
        .where(CartItem.id.in_(cart_item_ids))
        .with_for_update(of=CartItem)
    )

    if user_id:
        stmt = stmt.where(Cart.user_id == user_id)

    cart_items = (await session.execute(stmt)).scalars().all()
    return cart_items


async def update_cart_item_quantity_repo(
    update_cart_item_data: UpdateCartItemData,
    user_id: UUID | None,
    session: AsyncSession,
):
    stmt = (
        update(CartItem)
        .where(CartItem.id == update_cart_item_data.cart_item_id)
        .values(quantity=update_cart_item_data.new_quantity)
        .returning(CartItem)
    )

    if user_id:
        allowed_cart_ids = select(Cart.id).where(Cart.user_id == user_id)
        stmt = stmt.where(CartItem.cart_id.in_(allowed_cart_ids))

    updated_cart_item = (await session.execute(stmt)).scalar_one_or_none()
    return updated_cart_item


async def delete_cart_item_repo(
    cart_item_id: UUID, user_id: UUID | None, session: AsyncSession
):
    stmt = delete(CartItem).where(CartItem.id == cart_item_id).returning(CartItem)

    if user_id:
        allowed_cart_ids = select(Cart.id).where(Cart.user_id == user_id)
        stmt = stmt.where(CartItem.cart_id.in_(allowed_cart_ids))

    deleted_item = (await session.execute(stmt)).scalar_one_or_none()
    return deleted_item


async def delete_cart_repo(user_id: UUID, session: AsyncSession):
    deleted_cart_id = (
        await session.execute(
            delete(Cart).where(Cart.user_id == user_id).returning(Cart.id)
        )
    ).scalar_one_or_none()
    return deleted_cart_id


async def delete_cart_items_by_ids_repo(
    cart_item_ids: list[UUID], user_id: UUID | None, session: AsyncSession
):
    stmt = delete(CartItem).where(CartItem.id.in_(cart_item_ids)).returning(CartItem.id)

    if user_id:
        stmt = stmt.where(
            CartItem.cart_id.in_(select(Cart.id).where(Cart.user_id == user_id))
        )

    result = await session.execute(stmt)
    return result.scalars().all()
