import pytest

from app.repositories.review import get_product_reviews_list_db
from tests.factories.products import product_factory
from tests.factories.reviews import review_factory


@pytest.mark.asyncio
async def test_get_product_reviews_without_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(4)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()

    reviews, _ = await get_product_reviews_list_db(
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
    _, next_cursor = await get_product_reviews_list_db(
        new_product.id, None, None, 2, db_session
    )

    reviews, _ = await get_product_reviews_list_db(
        new_product.id, next_cursor["created_at"], next_cursor["id"], 2, db_session
    )

    assert reviews[-1][0] == new_reviews[3].id
    assert reviews[-1][2] == new_reviews[3].created_at
