from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_session
from app.repositories.products import get_random_product
from app.schemas.products import NewProductData, ProductData, ShortProductDataList, NewReviewData, ReviewDataList
from app.schemas.user import UserTokenData
from app.services.products import (
    add_product_in_market,
    create_product_review_serv,
    get_product_data_serv,
    get_product_list_serv,
    get_product_reviews_list_serv,
)

app = APIRouter(prefix="/product", tags=["Products"])


@app.get("/")
async def get_product_list_handler(
    created_at_cursor: datetime | None = Query(None),
    id_cursor: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ShortProductDataList:
    product_list = await get_product_list_serv(created_at_cursor, id_cursor, limit, session)
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
    product_data = await get_product_data_serv(product_id, session)
    return product_data


@app.get("/{product_id}/reviews")
async def get_product_reviews_list_handler(
    product_id: UUID,
    created_at_cursor: datetime | None = Query(None),
    id_cursor: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ReviewDataList:
    reviews_list = await get_product_reviews_list_serv(
        product_id, created_at_cursor, id_cursor, limit, session
    )
    return reviews_list


@app.post("/{product_id}/create_review")
async def create_product_review_handler(
    product_id: UUID,
    reviewData: NewReviewData,
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
):
    await create_product_review_serv(product_id, reviewData, token_data, session)
