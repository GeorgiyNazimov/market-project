from datetime import UTC, datetime, timedelta

import pytest

from app.database.models.product import Product
from app.database.models.review import Review
from app.repositories.product import get_product_list_repo, get_product_review_list_repo
from tests.factories.products import product_factory
from tests.factories.reviews import review_factory


@pytest.mark.asyncio
async def test_get_product_list_repo_without_cursor_success(db_session):
    products = [
        product_factory(created_at=datetime.utcnow() + timedelta(minutes=i))
        for i in range(4)
    ]
    db_session.add_all(products)
    await db_session.flush()

    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    expected_ids = [p.id for p in products]

    db_session.expunge_all()
    limit = 2
    product_list = await get_product_list_repo(
        sort_field=Product.created_at,
        last_value=None,
        last_id=None,
        limit=limit,
        session=db_session,
    )

    assert len(product_list) == limit
    for i in range(limit):
        assert product_list[i].id == expected_ids[i]
        assert hasattr(product_list[i], "product_rating")


@pytest.mark.asyncio
async def test_get_product_list_repo_pagination_success(db_session):
    products = [
        product_factory(created_at=datetime.utcnow() + timedelta(minutes=i))
        for i in range(6)
    ]
    db_session.add_all(products)
    await db_session.flush()

    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    expected_ids = [p.id for p in products]

    limit = 2
    last_value, last_id = None, None
    for i in range(3):
        db_session.expunge_all()
        product_list = await get_product_list_repo(
            sort_field=Product.created_at,
            last_value=last_value,
            last_id=last_id,
            limit=limit,
            session=db_session,
        )
        last_value = product_list[-1].created_at
        last_id = product_list[-1].id

        assert len(product_list) == limit
        for j in range(limit):
            assert product_list[j].id == expected_ids[j + limit * i]


@pytest.mark.asyncio
async def test_get_product_review_list_repo_without_cursor_success(db_session):
    product = product_factory()
    reviews = [
        review_factory(
            product=product, created_at=datetime.utcnow() + timedelta(minutes=i)
        )
        for i in range(4)
    ]
    db_session.add_all([product, *reviews])
    await db_session.flush()

    reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    expected_ids = [r.id for r in reviews]

    db_session.expunge_all()
    limit = 2
    review_list = await get_product_review_list_repo(
        sort_field=Review.created_at,
        product_id=product.id,
        last_value=None,
        last_id=None,
        limit=limit,
        session=db_session,
    )

    assert len(review_list) == limit
    for i in range(limit):
        assert review_list[i].id == expected_ids[i]


@pytest.mark.asyncio
async def test_get_product_review_list_repo_pagination_success(db_session):
    product = product_factory()
    reviews = [
        review_factory(
            product=product, created_at=datetime.utcnow() + timedelta(minutes=i)
        )
        for i in range(6)
    ]
    db_session.add_all([product, *reviews])
    await db_session.flush()

    reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    expected_ids = [r.id for r in reviews]

    limit = 2
    last_value, last_id = None, None
    for i in range(3):
        db_session.expunge_all()
        review_list = await get_product_review_list_repo(
            sort_field=Review.created_at,
            product_id=product.id,
            last_value=last_value,
            last_id=last_id,
            limit=limit,
            session=db_session,
        )
        last_value = review_list[-1].created_at
        last_id = review_list[-1].id

        assert len(review_list) == limit
        for j in range(limit):
            assert review_list[j].id == expected_ids[j + limit * i]
