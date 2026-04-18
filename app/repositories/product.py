import random
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import bindparam, func, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from app.database.models.product import Product
from app.database.models.product_avg_rating import ProductAverageRating
from app.database.models.review import Review
from app.database.models.user import User
from app.schemas.product import NewProductData, NewReviewData


async def get_product_list_repo(
    sort_field: Any,
    last_value: Any | None,
    last_id: UUID | None,
    limit: int,
    session: AsyncSession,
):
    stmt = (
        select(Product)
        .outerjoin(Product.product_rating)
        .options(contains_eager(Product.product_rating))
    )
    stmt = stmt.order_by(sort_field.desc().nullslast(), Product.id.desc()).limit(limit)

    if last_value is not None and last_id:
        stmt = stmt.where(tuple_(sort_field, Product.id) < (last_value, last_id))

    results = (await session.execute(stmt)).scalars().all()

    return results


async def get_product_data_repo(product_id: UUID, session: AsyncSession):
    product = (
        await session.execute(
            select(Product)
            .options(joinedload(Product.product_rating))
            .where(Product.id == product_id)
        )
    ).scalar_one_or_none()
    return product


async def update_product_average_rating_repo(
    product_id: UUID, rating: int, session: AsyncSession
):

    rating_counts = {f"rating_{i}_count": int(i == rating) for i in range(1, 6)}

    total_score_sql = sum(
        (
            getattr(ProductAverageRating, f"rating_{i}_count")
            + rating_counts[f"rating_{i}_count"]
        )
        * i
        for i in range(1, 6)
    )
    new_total_count = ProductAverageRating.rating_count + 1

    stmt = (
        insert(ProductAverageRating)
        .values(
            product_id=product_id,
            rating_count=1,
            avg_rating=rating,
            **rating_counts,
        )
        .on_conflict_do_update(
            index_elements=[ProductAverageRating.product_id],
            set_={
                **{
                    col: getattr(ProductAverageRating, col) + val
                    for col, val in rating_counts.items()
                },
                "rating_count": new_total_count,
                "avg_rating": total_score_sql / new_total_count,
            },
        )
    )

    await session.execute(stmt)


async def update_products_stock_repo(
    stock_update_data: list[dict], session: AsyncSession
):
    await session.execute(
        update(Product.__table__)
        .where(Product.id == bindparam("product_id"))
        .values(stock=Product.stock + bindparam("quantity")),
        stock_update_data,
        execution_options={"synchronize_session": False},
    )


# тестовая функция для добавления новых товаров в бд
async def create_product(new_product_data: NewProductData, session: AsyncSession):
    new_product = Product(
        name=new_product_data.name,
        price=new_product_data.price,
        stock=new_product_data.stock,
    )
    session.add(new_product)
    await session.commit()


cache_count = [0, datetime.now()]


# тестовая функция для получения случайного товара из бд
async def get_random_product(session: AsyncSession):
    if cache_count[0] == 0 or datetime.now() - cache_count[1] > timedelta(seconds=60):
        total = (await session.execute(select(func.count(Product.id)))).scalar_one()
        cache_count[0] = total
        cache_count[1] = datetime.now()

    if cache_count[0] == 0:
        return None

    offset = random.randint(0, cache_count[0] - 1)

    product = (
        await session.execute(select(Product).offset(offset).limit(1))
    ).scalar_one_or_none()
    return product


async def create_product_review_repo(
    new_review: Review,
    session: AsyncSession,
):
    session.add(new_review)
    await session.flush()


async def get_product_review_list_repo(
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


async def get_review_by_user_and_product_repo(product_id, user_id, session):
    res = await session.execute(
        select(Review).where(Review.product_id == product_id, Review.user_id == user_id)
    )
    return res.scalars().all()
