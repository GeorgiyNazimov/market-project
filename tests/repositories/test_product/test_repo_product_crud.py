from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.product import Product
from app.database.models.product_avg_rating import ProductAverageRating
from app.database.models.review import Review
from app.repositories.product import (
    create_product,
    create_product_review_repo,
    get_product_data_repo,
    update_product_average_rating_repo,
    update_products_stock_repo,
)
from tests.factories.products import new_product_data_factory, product_factory
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_product(db_session):
    new_product_data = new_product_data_factory()

    await create_product(new_product_data, db_session)

    product = (await db_session.execute(select(Product))).scalar_one()
    assert product.name == new_product_data.name
    assert product.price == new_product_data.price
    assert product.stock == new_product_data.stock


@pytest.mark.asyncio
async def test_get_product_data_repo_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    product_data = await get_product_data_repo(product.id, db_session)

    assert product_data.id == product.id
    assert product_data.name == product.name
    assert product_data.price == product.price
    assert product_data.product_rating is None


@pytest.mark.asyncio
async def test_get_product_data_repo_missing_id_returns_none(db_session):
    product_data = await get_product_data_repo(uuid4(), db_session)

    assert product_data is None


async def test_update_product_average_rating_repo_precision_check(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    ratings = [1, 5, 4, 3, 2, 5, 5, 4, 1, 2] * 10

    for val in ratings:
        await update_product_average_rating_repo(product.id, val, db_session)

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


@pytest.mark.asyncio
async def test_create_product_review_repo_success(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    review_data = new_review_data_factory()
    review = Review(
        text=review_data.text,
        product_rating=review_data.product_rating,
        product_id=product.id,
        user_id=user.id,
    )
    await create_product_review_repo(review, db_session)

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == product.id
    assert review.user_id == user.id
    assert review.text == review_data.text


@pytest.mark.parametrize("missing_entity", ["product", "user"])
@pytest.mark.asyncio
async def test_create_product_review_repo_fk_violation(db_session, missing_entity):
    product = product_factory()
    user = user_factory()

    if missing_entity == "user":
        db_session.add(product)
    else:
        db_session.add(user)

    await db_session.flush()

    review_data = new_review_data_factory()
    review = Review(
        text=review_data.text,
        product_rating=review_data.product_rating,
        product_id=product.id,
        user_id=user.id,
    )
    with pytest.raises(IntegrityError):
        await create_product_review_repo(review, db_session)
        await db_session.flush()
