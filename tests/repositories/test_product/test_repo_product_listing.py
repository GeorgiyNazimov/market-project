import pytest

from app.repositories.products import get_product_list_from_db
from tests.factories.products import multiple_products_factory


@pytest.mark.asyncio
async def test_get_product_list_without_cursor(db_session):
    new_products = multiple_products_factory(4)
    db_session.add_all(new_products)
    await db_session.flush()
    new_products.sort(key=lambda x: (x.created_at, x.id), reverse=True)

    product_list, _ = await get_product_list_from_db(
        None, None, limit=2, session=db_session
    )

    assert len(product_list) == 2
    assert product_list[-1].id == new_products[1].id
    assert product_list[-1].created_at == new_products[1].created_at


@pytest.mark.asyncio
async def test_get_product_list_with_cursor(db_session):
    new_products = multiple_products_factory(4)
    db_session.add_all(new_products)
    await db_session.flush()
    new_products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    _, next_cursor = await get_product_list_from_db(
        None, None, limit=2, session=db_session
    )

    product_list, next_cursor = await get_product_list_from_db(
        next_cursor["created_at"], next_cursor["id"], 2, db_session
    )

    assert len(product_list) == 2
    assert product_list[-1].id == new_products[3].id
    assert product_list[-1].created_at == new_products[3].created_at
