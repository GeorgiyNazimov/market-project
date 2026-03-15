from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.order import Order
from app.database.models.order_item import OrderItem


async def get_orders_by_user_id_repo(user_id: UUID, session: AsyncSession):
    stmt = (
        select(Order)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
        .where(Order.user_id == user_id)
    )

    orders = (await session.execute(stmt)).scalars().all()
    return orders


async def get_order_by_id_repo(
    order_id: UUID, user_id: UUID | None, session: AsyncSession
):
    stmt = (
        select(Order)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
        .where(Order.id == order_id)
    )

    if user_id:
        stmt = stmt.where(Order.user_id == user_id)

    order = (await session.execute(stmt)).scalar_one_or_none()
    return order


async def create_order_repo(user_id: UUID, session: AsyncSession):
    new_order = Order(user_id=user_id)
    session.add(new_order)
    await session.flush()
    return new_order


async def add_order_items_repo(order_items: list[OrderItem], session: AsyncSession):
    session.add_all(order_items)
    await session.flush()


async def update_order_total_price_repo(
    order_id: UUID, total_price: Decimal, session: AsyncSession
):
    result = await session.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(total_price=total_price)
        .returning(Order.id)
    )

    return result.scalar_one_or_none()


async def delete_order_repo(
    order_id: UUID, user_id: UUID | None, session: AsyncSession
):
    stmt = delete(Order).where(Order.id == order_id).returning(Order.id)

    if user_id:
        stmt = stmt.where(Order.user_id == user_id)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()
