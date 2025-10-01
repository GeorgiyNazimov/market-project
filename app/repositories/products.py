from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.database.models.user import User

async def get_product_list_from_db(session: AsyncSession):
    products = (await session.execute(select(Product))).scalars().all()
    return products

async def get_product_data_from_db(product_id: UUID, session: AsyncSession):
    product = (await session.execute(select(Product).where(Product.id == product_id))).scalar_one()
    return product

async def insert_cart_item(product_id: UUID, current_user: User, session: AsyncSession):
    try:
        cart = (await session.execute(select(Cart).where(Cart.user_id == current_user.id))).scalar()
        if cart is None:
            cart = Cart(user_id=current_user.id)
            session.add(cart)
            await session.flush()

        new_cart_item = CartItem(cart_id=cart.id, product_id=product_id)
        cart.total_items += 1
        session.add(new_cart_item)
        await session.commit()
        await session.refresh(new_cart_item)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            detail="This product already in your cart",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return new_cart_item