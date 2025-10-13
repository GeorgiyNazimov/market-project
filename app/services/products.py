from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.repositories.products import create_product, get_product_data_from_db, get_product_list_from_db, insert_cart_item
from app.schemas.products import NextCursorInfo, ProductData, ProductInfo, ShortProductData, ShortProductDataList

async def get_product_list(created_at_cursor: datetime | None, id_cursor: UUID | None, limit: int, session: AsyncSession) -> ShortProductDataList:
    products, next_cursor = await get_product_list_from_db(created_at_cursor, id_cursor, limit, session)
    products = [ShortProductData.model_validate(product) for product in products]
    next_cursor = NextCursorInfo.model_validate(next_cursor)
    return ShortProductDataList(product_list=products, next_cursor=next_cursor)

async def get_product_data(product_id: UUID, session: AsyncSession) -> ProductData:
    product = await get_product_data_from_db(product_id, session)
    return ProductData.model_validate(product)

async def add_product_in_cart(product_id: UUID, current_user: User, session: AsyncSession):
    new_cart_item = await insert_cart_item(product_id, current_user, session)
    return new_cart_item

#тестовая функция для добавления новых товаров в бд
async def add_product_in_market(productInfo: ProductInfo, session: AsyncSession):
    await create_product(productInfo, session)