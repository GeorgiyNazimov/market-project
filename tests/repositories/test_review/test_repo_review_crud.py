import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.review import Review
from app.repositories.review import create_product_review_db
from tests.factories.products import product_factory
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_review(db_session):
    new_product = product_factory()
    new_user = user_factory()
    new_review_data = new_review_data_factory()
    db_session.add_all([new_user, new_product])
    await db_session.flush()

    await create_product_review_db(
        new_product.id, new_review_data, new_user, db_session
    )

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == new_product.id
    assert review.user_id == new_user.id
    assert review.text == new_review_data.text


@pytest.mark.asyncio
async def test_cannot_create_review_for_unknown_product(db_session):
    new_product = product_factory()
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    new_review_data = new_review_data_factory()

    with pytest.raises(IntegrityError):
        await create_product_review_db(
            new_product.id, new_review_data, new_user, db_session
        )


@pytest.mark.asyncio
async def test_cannot_create_review_by_unknown_user(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_user = user_factory()
    await db_session.flush()
    new_review_data = new_review_data_factory()

    with pytest.raises(IntegrityError):
        await create_product_review_db(
            new_product.id, new_review_data, new_user, db_session
        )
