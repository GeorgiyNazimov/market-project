from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection.session import get_session
from app.repositories.products import get_random_product
from app.schemas.products import NewProductData, ProductData, ShortProductDataList
from app.services.products import (
    add_product_in_market,
    get_product_data,
    get_product_list,
)

app = APIRouter(prefix="/product", tags=["Products"])


@app.get("/")
async def get_product_list_handler(
    created_at_cursor: datetime | None = Query(None),
    id_cursor: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ShortProductDataList:
    product_list = await get_product_list(created_at_cursor, id_cursor, limit, session)
    return product_list


# тестовая ручка для добавления нового товара в магазин
@app.post("/trade")
async def add_product_in_market_handler(
    productInfo: NewProductData, session: AsyncSession = Depends(get_session)
):
    await add_product_in_market(productInfo, session)


# тестовая ручка для получения информации о случайном
@app.get("/random")
async def get_random_product_handler(
    session: AsyncSession = Depends(get_session),
) -> ProductData:
    rand_product = await get_random_product(session)
    return ProductData.model_validate(rand_product)


@app.get("/{product_id}")
async def get_product_data_handler(
    product_id: UUID, session: AsyncSession = Depends(get_session)
) -> ProductData:
    product_data = await get_product_data(product_id, session)
    return product_data
