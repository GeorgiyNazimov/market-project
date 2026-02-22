import random
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database.models.product import Product
from app.database.models.product_avg_rating import ProductAverageRating
from app.schemas.products import NewProductData


async def get_product_list_from_db(
    created_at_cursor: datetime | None,
    id_cursor: UUID | None,
    limit: int,
    session: AsyncSession,
):
    stmt = select(Product).options(selectinload(Product.product_rating))
    stmt = stmt.order_by(Product.created_at.desc(), Product.id.desc()).limit(limit)

    if created_at_cursor and id_cursor:
        stmt = stmt.where(
            tuple_(Product.created_at, Product.id) < (created_at_cursor, id_cursor)
        )

    results = (await session.execute(stmt)).scalars().all()

    next_cursor = None
    if results:
        last = results[-1]
        next_cursor = {"created_at": last.created_at, "id": last.id}

    return results, next_cursor


async def get_product_data_from_db(product_id: UUID, session: AsyncSession):
    product = (
        await session.execute(
            select(Product)
            .options(joinedload(Product.product_rating))
            .where(Product.id == product_id)
        )
    ).scalar_one()
    return product


async def update_product_average_rating(
    product_id: UUID, rating: int, session: AsyncSession
):

    rating_counts = {f"rating_{i}_count": int(i == rating) for i in range(1, 6)}

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
                "rating_count": ProductAverageRating.rating_count + 1,
                "avg_rating": (
                    (
                        ProductAverageRating.avg_rating
                        * ProductAverageRating.rating_count
                        + rating
                    )
                    / (ProductAverageRating.rating_count + 1)
                ),
            },
        )
    )

    await session.execute(stmt)


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
