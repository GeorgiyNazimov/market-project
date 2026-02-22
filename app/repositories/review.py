from datetime import datetime
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.review import Review
from app.database.models.user import User
from app.schemas.review import NewReviewData


async def create_product_review_db(
    product_id: UUID,
    reviewData: NewReviewData,
    current_user: User,
    session: AsyncSession,
):
    new_review = Review(
        text=reviewData.text,
        product_rating=reviewData.product_rating,
        product_id=product_id,
        user_id=current_user.id,
    )
    session.add(new_review)


async def get_product_reviews_list_db(
    product_id: UUID,
    created_at_cursor: datetime | None,
    id_cursor: UUID | None,
    limit: int,
    session: AsyncSession,
):
    stmt = (
        select(
            Review.id,
            Review.text,
            Review.created_at,
            Review.product_rating,
            User.first_name,
            User.last_name,
        )
        .join(User, Review.user_id == User.id)
        .where(Review.product_id == product_id)
    )

    if created_at_cursor and id_cursor:
        stmt = stmt.where(
            tuple_(Review.created_at, Review.id) < (created_at_cursor, id_cursor)
        )

    stmt = stmt.order_by(Review.created_at.desc(), Review.id.desc()).limit(limit)

    results = (await session.execute(stmt)).all()
    next_cursor = {"created_at": None, "id": None}
    if results:
        last = results[-1]
        next_cursor = {"created_at": last.created_at, "id": last.id}

    return results, next_cursor
