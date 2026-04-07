import pytest

from app.repositories.products import get_product_list_repo, get_product_reviews_list_repo
from tests.factories.products import multiple_products_factory, product_factory
from tests.factories.reviews import review_factory


@pytest.mark.asyncio
async def test_get_product_list_without_cursor(db_session):
    new_products = multiple_products_factory(4)
    db_session.add_all(new_products)
    await db_session.flush()
    new_products.sort(key=lambda x: (x.created_at, x.id), reverse=True)

    product_list, _ = await get_product_list_repo(
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
    _, next_cursor = await get_product_list_repo(
        None, None, limit=2, session=db_session
    )

    product_list, next_cursor = await get_product_list_repo(
        next_cursor["created_at"], next_cursor["id"], 2, db_session
    )

    assert len(product_list) == 2
    assert product_list[-1].id == new_products[3].id
    assert product_list[-1].created_at == new_products[3].created_at


@pytest.mark.asyncio
async def test_get_product_reviews_without_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(4)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()

    reviews, _ = await get_product_reviews_list_repo(
        new_product.id, None, None, 2, db_session
    )

    assert reviews[-1][0] == new_reviews[1].id
    assert reviews[-1][2] == new_reviews[1].created_at


@pytest.mark.asyncio
async def test_get_product_reviews_with_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(4)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()
    _, next_cursor = await get_product_reviews_list_repo(
        new_product.id, None, None, 2, db_session
    )

    reviews, _ = await get_product_reviews_list_repo(
        new_product.id, next_cursor["created_at"], next_cursor["id"], 2, db_session
    )

    assert reviews[-1][0] == new_reviews[3].id
    assert reviews[-1][2] == new_reviews[3].created_at
