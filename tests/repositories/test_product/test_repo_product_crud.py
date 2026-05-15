from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database.models.product import Product
from app.database.models.product_avg_rating import ProductAverageRating
from app.repositories.product import (
    create_product_repo,
    delete_product_repo,
    get_product_by_name_repo,
    get_product_repo,
    update_product_average_rating_repo,
    update_product_repo,
    update_products_stock_repo,
)
from tests.factories.products import (
    product_factory,
    product_update_data_factory,
)


@pytest.mark.asyncio
async def test_create_product_success(db_session):
    new_product = product_factory()

    await create_product_repo(new_product, db_session)

    product = (await db_session.execute(select(Product))).scalar_one()
    assert product.name == new_product.name
    assert product.price == new_product.price
    assert product.stock == new_product.stock


@pytest.mark.asyncio
async def test_get_product_data_repo_success(db_session):
    product = product_factory(product_rating_include=True)
    db_session.add(product)
    await db_session.flush()

    product_data = await get_product_repo(product.id, db_session)

    assert product_data.id == product.id
    assert product_data.name == product.name
    assert product_data.price == product.price
    assert product_data.product_rating.avg_rating == 0
    assert product_data.product_rating.rating_count == 0
    for i in range(1, 6):
        field = f"rating_{i}_count"
        assert getattr(product_data.product_rating, field) == 0


@pytest.mark.asyncio
async def test_get_product_data_repo_missing_id_returns_none(db_session):
    product_data = await get_product_repo(product_id=uuid4(), session=db_session)

    assert product_data is None


@pytest.mark.asyncio
async def test_get_product_by_name_repo_success(db_session):
    name = "product_name"
    product = product_factory(name)
    db_session.add(product)
    await db_session.flush()

    db_product = await get_product_by_name_repo(name, db_session)

    assert db_product.name == product.name
    assert db_product.price == product.price
    assert db_product.stock == product.stock


@pytest.mark.asyncio
async def test_get_product_by_name_repo_missing_name_returns_none(db_session):
    name = "missing_product_name"
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    db_product = await get_product_by_name_repo(name, db_session)

    assert db_product is None


@pytest.mark.asyncio
async def test_update_product_repo_success(db_session):
    product = product_factory()
    update_data = product_update_data_factory()
    db_session.add(product)
    await db_session.flush()

    update_data = update_data.model_dump(exclude_unset=True)
    updated_product = await update_product_repo(product.id, update_data, db_session)

    await db_session.refresh(product)
    assert product.id == updated_product.id
    assert product.name == update_data["name"]
    assert product.price == update_data["price"]


@pytest.mark.asyncio
async def test_update_product_repo_missing_product_id_returns_none(db_session):
    product = product_factory()
    update_data = product_update_data_factory()
    db_session.add(product)
    await db_session.flush()

    update_data = update_data.model_dump(exclude_unset=True)
    updated_product = await update_product_repo(
        product_id=uuid4(), update_data=update_data, session=db_session
    )

    assert updated_product is None


@pytest.mark.asyncio
async def test_delete_product_repo_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    deleted_id = await delete_product_repo(product.id, db_session)

    assert deleted_id == product.id


@pytest.mark.asyncio
async def test_delete_product_repo_missing_id_returns_none(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    deleted_id = await delete_product_repo(product_id=uuid4(), session=db_session)

    assert deleted_id is None


@pytest.mark.asyncio
async def test_update_product_average_rating_repo_create_review_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    db_avg = (
        await db_session.execute(
            select(ProductAverageRating).where(
                ProductAverageRating.product_id == product.id
            )
        )
    ).scalar_one_or_none()
    assert db_avg is None

    await update_product_average_rating_repo(
        product_id=product.id, new_rating=5, old_rating=None, session=db_session
    )

    await update_product_average_rating_repo(
        product_id=product.id, new_rating=2, old_rating=None, session=db_session
    )

    db_session.expunge_all()

    db_avg = (
        await db_session.execute(
            select(ProductAverageRating).where(
                ProductAverageRating.product_id == product.id
            )
        )
    ).scalar_one()
    assert db_avg is not None
    assert db_avg.rating_count == 2
    assert db_avg.rating_5_count == 1
    assert db_avg.rating_2_count == 1
    assert db_avg.avg_rating == pytest.approx(3.5)


@pytest.mark.asyncio
async def test_update_product_average_rating_repo_update_review_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    db_avg = (
        await db_session.execute(
            select(ProductAverageRating).where(
                ProductAverageRating.product_id == product.id
            )
        )
    ).scalar_one_or_none()
    assert db_avg is None

    await update_product_average_rating_repo(
        product_id=product.id, new_rating=5, old_rating=None, session=db_session
    )

    await update_product_average_rating_repo(
        product_id=product.id, new_rating=2, old_rating=5, session=db_session
    )

    db_session.expunge_all()

    db_avg = (
        await db_session.execute(
            select(ProductAverageRating).where(
                ProductAverageRating.product_id == product.id
            )
        )
    ).scalar_one()
    assert db_avg is not None
    assert db_avg.rating_count == 1
    assert db_avg.rating_5_count == 0
    assert db_avg.rating_2_count == 1
    assert db_avg.avg_rating == pytest.approx(2)


@pytest.mark.asyncio
async def test_update_product_average_rating_repo_delete_review_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    db_avg = (
        await db_session.execute(
            select(ProductAverageRating).where(
                ProductAverageRating.product_id == product.id
            )
        )
    ).scalar_one_or_none()
    assert db_avg is None

    await update_product_average_rating_repo(
        product_id=product.id, new_rating=5, old_rating=None, session=db_session
    )

    await update_product_average_rating_repo(
        product_id=product.id, new_rating=None, old_rating=5, session=db_session
    )

    db_session.expunge_all()

    db_avg = (
        await db_session.execute(
            select(ProductAverageRating).where(
                ProductAverageRating.product_id == product.id
            )
        )
    ).scalar_one()
    assert db_avg is not None
    assert db_avg.rating_count == 0
    assert db_avg.rating_5_count == 0
    assert db_avg.avg_rating == pytest.approx(0)


@pytest.mark.asyncio
async def test_update_product_average_rating_repo_precision_check(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    ratings = [1, 5, 4, 3, 2, 5, 5, 4, 1, 2] * 10

    for val in ratings:
        await update_product_average_rating_repo(product.id, val, None, db_session)

    res = await db_session.execute(
        select(ProductAverageRating).where(
            ProductAverageRating.product_id == product.id
        )
    )
    db_record = res.scalar_one()

    expected_count = len(ratings)
    expected_sum = sum(ratings)
    expected_avg = float(Decimal(expected_sum) / Decimal(expected_count))

    assert db_record.rating_count == expected_count
    assert db_record.avg_rating == pytest.approx(expected_avg, rel=1e-6)

    actual_db_rating_counts = (
        db_record.rating_1_count
        + db_record.rating_2_count
        + db_record.rating_3_count
        + db_record.rating_4_count
        + db_record.rating_5_count
    )
    assert actual_db_rating_counts == expected_count


@pytest.mark.asyncio
async def test_update_products_stock_repo_success(db_session):
    products = [product_factory() for _ in range(4)]
    db_session.add_all(products)
    await db_session.flush()

    initial_stock = {p.id: p.stock for p in products}

    stock_update_data = [
        {
            "product_id": product.id,
            "quantity": 3,
        }
        for product in products
    ]

    await update_products_stock_repo(stock_update_data, db_session)

    db_session.expunge_all()

    products = (await db_session.execute(select(Product))).scalars().all()
    for product in products:
        assert product.stock == initial_stock[product.id] + 3
