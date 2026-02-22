from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.database.models.user import User
from app.repositories.products import update_product_average_rating
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
    try:
        await create_product_review_db(product_id, reviewData, current_user, session)

        rating = reviewData.product_rating
        await update_product_average_rating(product_id, rating, session)
        await session.commit()
    except IntegrityError as e:
        sqlstate = getattr(e.orig, "sqlstate", None)
        if sqlstate == "23503":  # FK violation
            raise NotFoundError("User or Product not found") from e
        if sqlstate == "23505":  # unique violation
            raise ConflictError("You already wrote review for this product") from e
        raise


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
