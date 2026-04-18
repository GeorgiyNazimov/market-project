from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_session
from app.schemas.base import IdResponse, PaginationParams
from app.schemas.product import (
    NewProductData,
    NewReviewData,
    ProductData,
    ReviewDataList,
    ShortProductDataList,
)
from app.schemas.user import UserTokenData
from app.services.product import (
    add_product_in_market,
    create_product_review_serv,
    get_product_serv,
    get_product_list_serv,
    get_product_review_list_serv,
)

app = APIRouter(prefix="/products", tags=["Products"])


@app.get("/")
async def get_product_list_handler(
    pagination_params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
) -> ShortProductDataList:
    product_list = await get_product_list_serv(pagination_params, session)
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
    product_data = await get_product_serv(product_id, session)
    return product_data


@app.get("/{product_id}/reviews")
async def get_product_review_list_handler(
    product_id: UUID,
    pagination_params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
) -> ReviewDataList:
    review_list = await get_product_review_list_serv(
        product_id, pagination_params, session
    )
    return review_list


@app.post("/{product_id}/reviews")
async def create_product_review_handler(
    product_id: UUID,
    review_data: NewReviewData,
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
):
    await create_product_review_serv(product_id, review_data, token_data, session)
