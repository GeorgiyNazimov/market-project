from datetime import datetime, timedelta

import pytest

from app.core.exceptions import BadRequest
from app.services.review import get_review_list_serv
from tests.factories.base import pagination_params_factory
from tests.factories.products import product_factory
from tests.factories.reviews import review_factory


@pytest.mark.asyncio
async def test_get_product_review_list_serv_without_cursor_success(db_session):
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

    db_session.expunge_all()

    limit = 2
    pagination_params = pagination_params_factory(limit=limit)
    review_data_list = await get_review_list_serv(
        product.id, pagination_params, db_session
    )

    assert len(review_data_list.review_list) == limit
    for i in range(limit):
        assert review_data_list.review_list[i].id == expected_ids[i]


@pytest.mark.asyncio
async def test_get_product_review_list_serv_pagination_success(db_session):
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
    pagination_params = pagination_params_factory(limit=limit)
    for i in range(3):
        db_session.expunge_all()
        review_data_list = await get_review_list_serv(
            product.id, pagination_params, db_session
        )
        pagination_params.cursor = review_data_list.next_cursor

        assert len(review_data_list.review_list) == limit
        for j in range(limit):
            assert review_data_list.review_list[j].id == expected_ids[j + limit * i]


@pytest.mark.asyncio
async def test_get_product_review_list_serv_unsupported_sort_field_bad_request_error(
    db_session,
):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    limit = 2
    pagination_params = pagination_params_factory(sort_by="random_field", limit=limit)
    with pytest.raises(BadRequest):
        await get_review_list_serv(product.id, pagination_params, db_session)
