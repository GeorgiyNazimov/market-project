import logging
from datetime import datetime

from sqlalchemy import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, ConflictError, NotFoundError
from app.database.models.product_avg_rating import ProductAverageRating
from app.database.models.review import Review
from app.repositories.product import update_product_average_rating_repo
from app.repositories.review import (
    create_review_repo,
    delete_review_repo,
    get_review_by_id_repo,
    get_review_by_user_and_product_repo,
    get_review_list_repo,
    update_review_repo,
)
from app.schemas.base import PaginationParams
from app.schemas.review import (
    NewReviewData,
    ReviewData,
    ReviewDataList,
    ReviewUpdateData,
)
from app.schemas.user import UserTokenData
from app.utils.logging import get_schema_diff
from app.utils.pagination import decode_cursor, encode_cursor

logger = logging.getLogger("service.review")
REVIEW_SORT_CONFIG = {
    "created_at": (Review.created_at, datetime.fromisoformat, lambda r: r.created_at),
}


def get_product_rating_log_data(product_rating: ProductAverageRating) -> dict:
    if not product_rating:
        return {}
    return {
        "product_rating_snapshot": {
            "avg": product_rating.avg_rating,
            "total": product_rating.rating_count,
            "details": {
                str(i): getattr(product_rating, f"rating_{i}_count")
                for i in range(1, 6)
            },
        }
    }


async def create_review_serv(
    product_id: UUID,
    review_data: NewReviewData,
    token_data: UserTokenData,
    session: AsyncSession,
):
    existing = await get_review_by_user_and_product_repo(
        product_id, token_data.id, session
    )
    if existing:
        raise ConflictError("You already wrote review for this product")

    try:
        new_review = Review(
            text=review_data.text,
            product_rating=review_data.product_rating,
            product_id=product_id,
            user_id=token_data.id,
        )
        await create_review_repo(new_review, session)
        await session.flush()

        rating = review_data.product_rating
        updated_product_rating = await update_product_average_rating_repo(
            product_id, rating, None, session
        )
        product_rating_snapshot = get_product_rating_log_data(updated_product_rating)
        await session.commit()
        logger.info(
            "review_create_success",
            extra={
                "product_id": product_id,
                "review_id": new_review.id,
                "user_rating": new_review.product_rating,
                **product_rating_snapshot,
            },
        )
        return new_review
    except IntegrityError as e:
        await session.rollback()
        sqlstate = getattr(e.orig, "sqlstate", None)
        if sqlstate == "23503":  # FK violation
            raise NotFoundError("Product not found") from e
        if sqlstate == "23505":  # unique violation
            raise ConflictError("You already wrote review for this product") from e
        raise

    except Exception as e:
        await session.rollback()
        raise


async def get_review_list_serv(
    product_id: UUID,
    pagination_params: PaginationParams,
    session: AsyncSession,
) -> ReviewDataList:
    sort_by = pagination_params.sort_by
    cursor = pagination_params.cursor
    limit = pagination_params.limit

    config = REVIEW_SORT_CONFIG.get(sort_by)
    if not config:
        raise BadRequest(f"Sorting by {sort_by} is not supported")

    sort_field, parse_func, get_val = config
    last_value, last_id = decode_cursor(cursor, parse_func) if cursor else (None, None)

    review_list = await get_review_list_repo(
        product_id, sort_field, last_value, last_id, limit + 1, session
    )
    review_list = [ReviewData.model_validate(review) for review in review_list]

    next_cursor = None
    if len(review_list) > limit:
        review_list = review_list[:limit]
        last = review_list[-1]
        next_cursor = encode_cursor({"v": get_val(last), "i": last.id})

    return ReviewDataList(review_list=review_list, next_cursor=next_cursor)


async def update_review_serv(
    review_id: UUID,
    review_update_data: ReviewUpdateData,
    token_data: UserTokenData,
    session: AsyncSession,
):
    old_review = await get_review_by_id_repo(review_id, session)
    if old_review is None:
        raise NotFoundError("Review not found")

    old_snapshot = ReviewUpdateData.model_validate(old_review)

    owner_id = None if token_data.role == "admin" else token_data.id

    update_data = review_update_data.model_dump(exclude_unset=True)
    if not update_data:
        raise BadRequest("No data provided for update")

    try:
        product_rating_snapshot = {}
        new_rating = update_data.get("product_rating")
        old_rating = old_review.product_rating
        if new_rating is not None and old_rating != new_rating:
            updated_product_rating = await update_product_average_rating_repo(
                product_id=old_review.product_id,
                new_rating=new_rating,
                old_rating=old_rating,
                session=session,
            )
            product_rating_snapshot = get_product_rating_log_data(
                updated_product_rating
            )

        updated_review = await update_review_repo(
            review_id, owner_id, update_data, session
        )
        if updated_review is None:
            await session.rollback()
            raise NotFoundError("Review not found")

        new_snapshot = ReviewUpdateData.model_validate(updated_review)

        changes = get_schema_diff(old_snapshot, new_snapshot)

        await session.commit()
        logger.info(
            "review_update_success",
            extra={
                "is_admin": token_data.role == "admin",
                "review_id": review_id,
                "diff": changes,
                **product_rating_snapshot,
            },
        )
        return updated_review.id
    except Exception:
        await session.rollback()
        raise


async def delete_review_serv(
    review_id: UUID, token_data: UserTokenData, session: AsyncSession
):
    review = await get_review_by_id_repo(review_id, session)
    if review is None:
        raise NotFoundError("Review not found")

    owner_id = None if token_data.role == "admin" else token_data.id

    try:
        deleted_id = await delete_review_repo(review_id, owner_id, session)
        if deleted_id is None:
            await session.rollback()
            raise NotFoundError("Review not found")

        old_rating = review.product_rating
        updated_product_rating = await update_product_average_rating_repo(
            product_id=review.product_id,
            new_rating=None,
            old_rating=old_rating,
            session=session,
        )
        product_rating_snapshot = get_product_rating_log_data(updated_product_rating)

        await session.commit()
        logger.info(
            "review_delete_success",
            extra={
                "is_admin": token_data.role == "admin",
                "review_id": review_id,
                "product_id": review.product_id,
                **product_rating_snapshot,
            },
        )
        return deleted_id
    except Exception:
        await session.rollback()
        raise
