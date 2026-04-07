import pytest

from app.services.products import get_product_list_serv, get_product_reviews_list_serv
from tests.factories.products import multiple_products_factory, product_factory
from tests.factories.reviews import review_factory


@pytest.mark.asyncio
async def test_get_product_list_without_cursor(db_session):
    new_products = multiple_products_factory(4)
    db_session.add_all(new_products)
    await db_session.flush()
    new_products.sort(key=lambda x: (x.created_at, x.id), reverse=True)

    products = await get_product_list_serv(None, None, limit=2, session=db_session)

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
    products = await get_product_list_serv(None, None, limit=2, session=db_session)

    products = await get_product_list_serv(
        products.next_cursor.created_at, products.next_cursor.id, 2, db_session
    )

    assert len(products.product_list) == 2
    assert products.product_list[-1].id == new_products[3].id
    assert products.product_list[-1].created_at == new_products[3].created_at
    assert products.next_cursor.id == new_products[3].id
    assert products.next_cursor.created_at == new_products[3].created_at


limit = 4

@pytest.mark.asyncio
async def test_get_product_reviews_without_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(limit)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()

    review_data_list = await get_product_reviews_list_serv(
        new_product.id, None, None, limit / 2, db_session
    )

    assert (
        review_data_list.reviews_list[-1].created_at
        == new_reviews[(limit // 2) - 1].created_at
    )


@pytest.mark.asyncio
async def test_get_product_reviews_with_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(limit)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()
    review_data_list = await get_product_reviews_list_serv(
        new_product.id, None, None, limit / 2, db_session
    )

    review_data_list = await get_product_reviews_list_serv(
        new_product.id,
        review_data_list.next_cursor.created_at,
        review_data_list.next_cursor.id,
        limit / 2,
        db_session,
    )

    assert (
        review_data_list.reviews_list[-1].created_at
        == new_reviews[limit - 1].created_at
    )
