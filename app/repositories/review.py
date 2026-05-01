from typing import Any
from uuid import UUID

from sqlalchemy import delete, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database.models.review import Review


async def create_review_repo(
    new_review: Review,
    session: AsyncSession,
):
    session.add(new_review)
    await session.flush()


async def get_review_by_id_repo(review_id: UUID, session: AsyncSession):
    return await session.get(Review, review_id)


async def get_review_list_repo(
    product_id: UUID,
    sort_field: Any,
    last_value: Any | None,
    last_id: UUID | None,
    limit: int,
    session: AsyncSession,
):
    stmt = (
        select(Review)
        .options(joinedload(Review.user))
        .where(Review.product_id == product_id)
    )
    stmt = stmt.order_by(sort_field.desc().nullslast(), Review.id.desc()).limit(limit)

    if last_value is not None and last_id:
        stmt = stmt.where(tuple_(sort_field, Review.id) < (last_value, last_id))

    results = (await session.execute(stmt)).scalars().all()
    return results


async def get_review_by_user_and_product_repo(
    product_id: UUID, user_id: UUID, session: AsyncSession
):
    res = await session.execute(
        select(Review).where(Review.product_id == product_id, Review.user_id == user_id)
    )
    return res.scalars().all()


async def update_review_repo(
    review_id: UUID, user_id: UUID | None, update_data: dict, session: AsyncSession
):
    stmt = (
        update(Review)
        .where(Review.id == review_id)
        .values(**update_data)
        .returning(Review.id)
    )

    if user_id is not None:
        stmt = stmt.where(Review.user_id == user_id)

    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def delete_review_repo(
    review_id: UUID, user_id: UUID | None, session: AsyncSession
):
    stmt = delete(Review).where(Review.id == review_id).returning(Review.id)

    if user_id is not None:
        stmt = stmt.where(Review.user_id == user_id)

    res = await session.execute(stmt)
    return res.scalar_one_or_none()
