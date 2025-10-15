from datetime import datetime, timedelta
import random
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.database.models.user import User
from app.schemas.cart import UpdateCartItemData

async def get_cart(current_user: User, session: AsyncSession):
    cart = (await session.execute(select(Cart).where(Cart.user_id == current_user.id))).scalar()
    if cart is None:
        cart = Cart(user_id=current_user.id)
        session.add(cart)
        await session.commit()
    return cart

async def get_cart_items_from_db(current_user: User, session: AsyncSession):
    cart = await get_cart(current_user, session)
    cart_items = (await session.execute(select(
            CartItem.quantity.label("quantity"),
            CartItem.product_id,
            CartItem.id,
            Product.name.label("name"),
            Product.price.label("price"),
            (Product.price * CartItem.quantity).label("total_price")
        )
        .join(Cart, Cart.id == CartItem.cart_id)
        .join(Product, CartItem.product_id == Product.id)
        .where(Cart.id == cart.id)
    )).all()
    return cart_items

async def insert_cart_item(product_id: UUID, current_user: User, session: AsyncSession):
    try:
        cart = await get_cart(current_user, session)

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

async def update_cart_item_quatity_in_db(update_cartitem_data: UpdateCartItemData, session: AsyncSession):
    cart_item = await session.get(CartItem, update_cartitem_data.cart_item_id)
    cart_item.quantity = update_cartitem_data.new_quantity
    await session.commit()

async def delete_cart_item_from_db(cart_item_id: UUID, session: AsyncSession):
    await session.execute(delete(CartItem).where(CartItem.id == cart_item_id))
    await session.commit()

async def delete_cart_from_db(current_user: User, session: AsyncSession):
    cart = await get_cart(current_user, session)
    await session.delete(cart)
    await session.commit()