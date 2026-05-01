from typing import Any
from uuid import UUID

from sqlalchemy import bindparam, case, delete, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from app.database.models.product import Product
from app.database.models.product_avg_rating import ProductAverageRating


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


async def create_product_repo(new_product: Product, session: AsyncSession):
    session.add(new_product)
    await session.flush()


async def get_product_repo(product_id: UUID, session: AsyncSession):
    product = (
        await session.execute(
            select(Product)
            .options(joinedload(Product.product_rating))
            .where(Product.id == product_id)
        )
    ).scalar_one_or_none()
    return product


async def update_product_repo(
    product_id: UUID, update_data: dict, session: AsyncSession
) -> UUID | None:
    stmt = (
        update(Product)
        .where(Product.id == product_id)
        .values(**update_data)
        .returning(Product.id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_product_repo(product_id: UUID, session: AsyncSession) -> UUID | None:
    stmt = delete(Product).where(Product.id == product_id).returning(Product.id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_product_by_name_repo(name: str, session: AsyncSession):
    res = await session.execute(select(Product).where(Product.name == name).limit(1))
    return res.scalar_one_or_none()


async def update_product_average_rating_repo(
    product_id: UUID,
    new_rating: int | None,
    old_rating: int | None,
    session: AsyncSession,
):
    count_delta = (1 if new_rating else 0) - (1 if old_rating else 0)
    initial_counts = {
        f"rating_{i}_count": (1 if i == new_rating else 0) for i in range(1, 6)
    }

    deltas = {f"rating_{i}_count": 0 for i in range(1, 6)}
    if new_rating:
        deltas[f"rating_{new_rating}_count"] += 1
    if old_rating:
        deltas[f"rating_{old_rating}_count"] -= 1

    total_score_sql = sum(
        (
            getattr(ProductAverageRating, f"rating_{i}_count")
            + deltas[f"rating_{i}_count"]
        )
        * i
        for i in range(1, 6)
    )
    new_total_count = ProductAverageRating.rating_count + count_delta

    stmt = (
        insert(ProductAverageRating)
        .values(
            product_id=product_id,
            rating_count=1 if new_rating else 0,
            avg_rating=new_rating or 0,
            **initial_counts,
        )
        .on_conflict_do_update(
            index_elements=[ProductAverageRating.product_id],
            set_={
                **{
                    col: getattr(ProductAverageRating, col) + val
                    for col, val in deltas.items()
                    if val != 0
                },
                "rating_count": new_total_count,
                "avg_rating": total_score_sql
                / case((new_total_count == 0, 1), else_=new_total_count),
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
