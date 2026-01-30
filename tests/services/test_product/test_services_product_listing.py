import pytest

from app.services.products import get_product_list
from tests.factories.products import multiple_products_factory


@pytest.mark.asyncio
async def test_get_product_list_without_cursor(db_session):
    new_products = multiple_products_factory(4)
    db_session.add_all(new_products)
    await db_session.flush()
    new_products.sort(key=lambda x: (x.created_at, x.id), reverse=True)

    products = await get_product_list(None, None, limit=2, session=db_session)

    assert len(products.product_list) == 2
    assert products.product_list[-1].id == new_products[1].id
    assert products.product_list[-1].created_at == new_products[1].created_at
    assert products.next_cursor.id == new_products[1].id
    assert products.next_cursor.created_at == new_products[1].created_at


@pytest.mark.asyncio
async def test_get_product_list_with_cursor(db_session):
    new_products = multiple_products_factory(4)
    db_session.add_all(new_products)
    await db_session.flush()
    new_products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    products = await get_product_list(None, None, limit=2, session=db_session)

    products = await get_product_list(
        products.next_cursor.created_at, products.next_cursor.id, 2, db_session
    )

    assert len(products.product_list) == 2
    assert products.product_list[-1].id == new_products[3].id
    assert products.product_list[-1].created_at == new_products[3].created_at
    assert products.next_cursor.id == new_products[3].id
    assert products.next_cursor.created_at == new_products[3].created_at
