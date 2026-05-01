from datetime import datetime, timedelta

import pytest

from app.database.models.product import Product
from app.repositories.product import get_product_list_repo
from tests.factories.products import product_factory


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
