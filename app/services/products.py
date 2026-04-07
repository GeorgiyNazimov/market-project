from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.products import (
    create_product,
    create_product_review_repo,
    get_product_data_repo,
    get_product_list_repo,
    get_product_reviews_list_repo,
    update_product_average_rating_repo,
)
from app.schemas.products import (
    NewProductData,
    NextCursorData,
    ProductData,
    ShortProductData,
    ShortProductDataList,
    NewReviewData,
    ReviewData,
    ReviewDataList,
)
from app.schemas.user import UserTokenData


async def get_product_list_serv(
    created_at_cursor: datetime | None,
    id_cursor: UUID | None,
    limit: int,
    session: AsyncSession,
) -> ShortProductDataList:
    products, next_cursor = await get_product_list_repo(
        created_at_cursor, id_cursor, limit, session
    )
    products = [ShortProductData.model_validate(product) for product in products]
    next_cursor = NextCursorData.model_validate(next_cursor)
    return ShortProductDataList(product_list=products, next_cursor=next_cursor)


async def get_product_data_serv(product_id: UUID, session: AsyncSession) -> ProductData:
    product = await get_product_data_repo(product_id, session)
    return ProductData.model_validate(product)


# тестовая функция для добавления новых товаров в бд
async def add_product_in_market(productInfo: NewProductData, session: AsyncSession):
    await create_product(productInfo, session)


async def create_product_review_serv(
    product_id: UUID,
    reviewData: NewReviewData,
    token_data: UserTokenData,
    session: AsyncSession,
):
    try:
        await create_product_review_repo(product_id, reviewData, token_data, session)

        rating = reviewData.product_rating
        await update_product_average_rating_repo(product_id, rating, session)
        await session.commit()
    except IntegrityError as e:
        sqlstate = getattr(e.orig, "sqlstate", None)
        if sqlstate == "23503":  # FK violation
            raise NotFoundError("User or Product not found") from e
        if sqlstate == "23505":  # unique violation
            raise ConflictError("You already wrote review for this product") from e
        raise


async def get_product_reviews_list_serv(
    product_id: UUID,
    created_at_cursor: datetime,
    id_cursor: UUID,
    limit: int,
    session: AsyncSession,
) -> ReviewDataList:
    reviews_list, next_cursor = await get_product_reviews_list_repo(
        product_id, created_at_cursor, id_cursor, limit, session
    )
    reviews_list = [ReviewData.model_validate(review) for review in reviews_list]
    next_cursor = NextCursorData.model_validate(next_cursor)
    return ReviewDataList(reviews_list=reviews_list, next_cursor=next_cursor)
