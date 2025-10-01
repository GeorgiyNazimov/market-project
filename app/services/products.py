from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.repositories.products import get_product_data_from_db, get_product_list_from_db, insert_cart_item
from app.schemas.products import ProductData, ShortProductData, ShortProductDataList

async def get_product_list(session: AsyncSession) -> ShortProductDataList:
    products = await get_product_list_from_db(session)
    products = [ShortProductData.model_validate(product) for product in products]
    return ShortProductDataList(product_list=products)

async def get_product_data(product_id: UUID, session: AsyncSession) -> ProductData:
    product = await get_product_data_from_db(product_id, session)
    return ProductData.model_validate(product)

async def add_product_in_cart(product_id: UUID, current_user: User, session: AsyncSession):
    new_cart_item = await insert_cart_item(product_id, current_user, session)
    return new_cart_item