from datetime import datetime
from uuid import UUID
from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.review import Review
from app.database.models.user import User
from app.database.models.product_avg_rating import ProductAverageRating
from app.schemas.review import NewReviewData


async def create_product_review_db(
    product_id: UUID,
    reviewData: NewReviewData,
    current_user: User,
    session: AsyncSession
):
    try:
        new_review = Review(
            text=reviewData.text,
            product_rating=reviewData.product_rating,
            product_id=product_id,
            user_id=current_user.id
        )
        session.add(new_review)
        rating = new_review.product_rating
        stmt = insert(ProductAverageRating).values(
            product_id=product_id,
            rating_1_count = 1 if rating == 1 else 0,
            rating_2_count = 1 if rating == 2 else 0,
            rating_3_count = 1 if rating == 3 else 0,
            rating_4_count = 1 if rating == 4 else 0,
            rating_5_count = 1 if rating == 5 else 0,
            rating_count = 1,
            avg_rating = rating
        ).on_conflict_do_update(
            index_elements=[ProductAverageRating.product_id],
            set_={
                "rating_1_count":
                    ProductAverageRating.rating_1_count + int(rating == 1),
                "rating_2_count":
                    ProductAverageRating.rating_2_count + int(rating == 2),
                "rating_3_count":
                    ProductAverageRating.rating_3_count + int(rating == 3),
                "rating_4_count":
                    ProductAverageRating.rating_4_count + int(rating == 4),
                "rating_5_count":
                    ProductAverageRating.rating_5_count + int(rating == 5),
                "rating_count":
                    ProductAverageRating.rating_count + 1,
                "avg_rating":
                    (
                        (ProductAverageRating.avg_rating * ProductAverageRating.rating_count + rating)
                        / (ProductAverageRating.rating_count + 1)
                    ),
            },
        )

        await session.execute(stmt)
        await session.commit()
    except:
        await session.rollback()
        raise

async def get_product_reviews_list_db(
    product_id: UUID,
    created_at_cursor: datetime | None,
    id_cursor: UUID | None,
    limit: int,
    session: AsyncSession
):
    stmt = (select(Review.id, Review.text, Review.created_at, Review.product_rating, User.first_name, User.last_name)
        .join(User, Review.user_id == User.id)
        .where(Review.product_id == product_id)
        )

    if created_at_cursor and id_cursor:
        stmt = (stmt
            .where(tuple_(Review.created_at, Review.id) < (created_at_cursor, id_cursor))
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(limit)
        )
    else:
        stmt = (stmt
            .order_by(Review.created_at.desc(), Review.id.desc())
            .limit(limit)
        )
    
    results = (await session.execute(stmt)).all()
    next_cursor = {
            "created_at": None,
            "id": None
        }
    if results:
        last = results[-1]
        next_cursor = {
            "created_at": last.created_at.isoformat(),
            "id": str(last.id)
        }
    
    return results, next_cursor