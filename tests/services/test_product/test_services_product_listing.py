import pytest

from app.core.exceptions import BadRequest
from app.services.product import get_product_list_serv
from tests.factories.base import pagination_params_factory
from tests.factories.products import multiple_products_factory


@pytest.mark.asyncio
async def test_get_product_list_serv_without_cursor_success(db_session):
    products = multiple_products_factory(6)
    db_session.add_all(products)
    await db_session.flush()

    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    expected_ids = [p.id for p in products]

    db_session.expunge_all()

    limit = 2
    pagination_params = pagination_params_factory(limit=limit)
    product_data_list = await get_product_list_serv(pagination_params, db_session)

    assert len(product_data_list.product_list) == limit
    for i in range(limit):
        assert product_data_list.product_list[i].id == expected_ids[i]


@pytest.mark.asyncio
async def test_get_product_list_serv_pagination_success(db_session):
    products = multiple_products_factory(6)
    db_session.add_all(products)
    await db_session.flush()

    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    expected_ids = [p.id for p in products]

    limit = 2
    pagination_params = pagination_params_factory(limit=limit)
    for i in range(3):
        db_session.expunge_all()
        product_data_list = await get_product_list_serv(pagination_params, db_session)
        pagination_params.cursor = product_data_list.next_cursor

        assert len(product_data_list.product_list) == limit
        for j in range(limit):
            assert product_data_list.product_list[j].id == expected_ids[j + limit * i]


@pytest.mark.asyncio
async def test_get_product_list_serv_unsupported_sort_field_bad_request_error(
    db_session,
):
    limit = 2
    pagination_params = pagination_params_factory(sort_by="random_field", limit=limit)
    with pytest.raises(BadRequest):
        await get_product_list_serv(pagination_params, db_session)
