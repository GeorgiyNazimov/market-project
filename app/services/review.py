from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.repositories.review import (
    create_product_review_db,
    get_product_reviews_list_db,
)
from app.schemas.review import NewReviewData, NextCursorData, ReviewData, ReviewDataList


async def create_product_review(
    product_id: UUID,
    reviewData: NewReviewData,
    current_user: User,
    session: AsyncSession,
):
    await create_product_review_db(product_id, reviewData, current_user, session)


async def get_product_reviews_list(
    product_id: UUID,
    created_at_cursor: datetime,
    id_cursor: UUID,
    limit: int,
    session: AsyncSession,
) -> ReviewDataList:
    reviews_list, next_cursor = await get_product_reviews_list_db(
        product_id, created_at_cursor, id_cursor, limit, session
    )
    reviews_list = [ReviewData.model_validate(review) for review in reviews_list]
    next_cursor = NextCursorData.model_validate(next_cursor)
    return ReviewDataList(reviews_list=reviews_list, next_cursor=next_cursor)
