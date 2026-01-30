from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.products import (
    create_product,
    get_product_data_from_db,
    get_product_list_from_db,
)
from app.schemas.products import (
    NewProductData,
    NextCursorData,
    ProductData,
    ShortProductData,
    ShortProductDataList,
)


async def get_product_list(
    created_at_cursor: datetime | None,
    id_cursor: UUID | None,
    limit: int,
    session: AsyncSession,
) -> ShortProductDataList:
    products, next_cursor = await get_product_list_from_db(
        created_at_cursor, id_cursor, limit, session
    )
    products = [ShortProductData.model_validate(product) for product in products]
    next_cursor = NextCursorData.model_validate(next_cursor)
    return ShortProductDataList(product_list=products, next_cursor=next_cursor)


async def get_product_data(product_id: UUID, session: AsyncSession) -> ProductData:
    product = await get_product_data_from_db(product_id, session)
    return ProductData.model_validate(product)


# тестовая функция для добавления новых товаров в бд
async def add_product_in_market(productInfo: NewProductData, session: AsyncSession):
    await create_product(productInfo, session)
