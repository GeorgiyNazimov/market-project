import pytest

from app.services.review import get_product_reviews_list
from tests.factories.products import product_factory
from tests.factories.reviews import review_factory

limit = 4

@pytest.mark.asyncio
async def test_get_product_reviews_without_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(limit)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()
    
    review_data_list = await get_product_reviews_list(new_product.id, None, None, limit/2, db_session)

    assert review_data_list.reviews_list[-1].created_at == new_reviews[(limit//2) - 1].created_at

@pytest.mark.asyncio
async def test_get_product_reviews_with_cursor(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_reviews = [review_factory(product=new_product) for i in range(limit)]
    new_reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(new_reviews)
    await db_session.flush()
    review_data_list = await get_product_reviews_list(new_product.id, None, None, limit/2, db_session)
    
    review_data_list = await get_product_reviews_list(
        new_product.id,
        review_data_list.next_cursor.created_at,
        review_data_list.next_cursor.id,
        limit/2,
        db_session
        )
    
    assert review_data_list.reviews_list[-1].created_at == new_reviews[limit-1].created_at