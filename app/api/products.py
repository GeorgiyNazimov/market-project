from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_session
from app.schemas.base import IdResponse, PaginationParams
from app.schemas.product import (
    NewProductData,
    ProductData,
    ProductUpdateData,
    ShortProductDataList,
)
from app.schemas.review import NewReviewData, ReviewDataList
from app.schemas.user import UserTokenData
from app.services.product import (
    create_product_serv,
    delete_product_serv,
    get_product_list_serv,
    get_product_serv,
    update_product_serv,
)
from app.services.review import create_review_serv, get_review_list_serv

app = APIRouter(prefix="/products", tags=["Products"])


@app.get("/")
async def get_product_list_handler(
    pagination_params: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_session),
) -> ShortProductDataList:
    product_list = await get_product_list_serv(pagination_params, session)
    return product_list


@app.post("/")
async def create_product_handler(
    product_data: NewProductData,
    token_data: UserTokenData = Depends(RoleChecker(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    product_id = await create_product_serv(product_data, session)
    return IdResponse(id=product_id)


@app.patch("/{product_id}")
async def update_product_handler(
    product_id: UUID,
    product_update_data: ProductUpdateData,
    token_data: UserTokenData = Depends(RoleChecker(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    updated_id = await update_product_serv(product_id, product_update_data, session)
    return IdResponse(id=updated_id)


@app.delete("/{product_id}")
async def delete_product_handler(
    product_id: UUID,
    token_data: UserTokenData = Depends(RoleChecker(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    deleted_id = await delete_product_serv(product_id, session)
    return IdResponse(id=deleted_id)


@app.get("/{product_id}")
async def get_product_handler(
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
    review_list = await get_review_list_serv(product_id, pagination_params, session)
    return review_list


@app.post("/{product_id}/reviews")
async def create_product_review_handler(
    product_id: UUID,
    review_data: NewReviewData,
    token_data: UserTokenData = Depends(RoleChecker(["user"])),
    session: AsyncSession = Depends(get_session),
):
    new_review = await create_review_serv(product_id, review_data, token_data, session)
    return new_review
