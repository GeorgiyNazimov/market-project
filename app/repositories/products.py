from datetime import datetime, timedelta
import random
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.database.models.user import User
from app.schemas.products import ProductInfo

async def get_product_list_from_db(created_at_cursor: datetime | None, id_cursor: UUID | None, limit: int, session: AsyncSession):
    stmt = select(Product)

    if created_at_cursor and id_cursor:
        # Запрос новой партии информации о товарах
        stmt = (stmt
            .where(tuple_(Product.created_at, Product.id) < (created_at_cursor, id_cursor))
            .order_by(Product.created_at.desc(), Product.id.desc())
            .limit(limit)
        )
    else:
        # Самый первый запрос без курсора
        stmt = stmt.order_by(Product.created_at.desc(), Product.id.desc()).limit(limit)
    results = (await session.execute(stmt)).scalars().all()
    next_cursor = None
    if results:
        last = results[-1]
        next_cursor = {
            "created_at": last.created_at.isoformat(),
            "id": str(last.id)
        }
    return results, next_cursor

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

#тестовая функция для добавления новых товаров в бд
async def create_product(productInfo: ProductInfo, session: AsyncSession):
    new_product = Product(name=productInfo.name, price=productInfo.price, stock=productInfo.stock)
    session.add(new_product)
    await session.commit()

cache_count = [0, datetime.now()]

#тестовая функция для получения случайного товара из бд
async def get_random_product(session: AsyncSession):
    if cache_count[0] == 0 or datetime.now() - cache_count[1] > timedelta(seconds=60):
        total = (await session.execute(select(func.count(Product.id)))).scalar_one()
        cache_count[0] = total
        cache_count[1] = datetime.now()
    
    if cache_count[0] == 0:
        return None
    
    offset = random.randint(0, cache_count[0] - 1)

    product = (await session.execute(select(Product).offset(offset).limit(1))).scalar_one_or_none()
    return product