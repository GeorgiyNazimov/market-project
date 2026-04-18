from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.exceptions import ConflictError, NotFoundError
from app.database.models.product import Product
from app.database.models.review import Review
from app.services.product import (
    add_product_in_market,
    create_product_review_serv,
    get_product_serv,
)
from tests.factories.products import new_product_data_factory, product_factory
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import token_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_product(db_session):
    new_product_data = new_product_data_factory()

    await add_product_in_market(new_product_data, db_session)

    product = (await db_session.execute(select(Product))).scalar_one()
    assert product.name == new_product_data.name
    assert product.price == new_product_data.price
    assert product.stock == new_product_data.stock


@pytest.mark.asyncio
async def test_get_product_data_serv_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    product_data = await get_product_serv(product.id, db_session)

    assert product_data.id == product.id
    assert product_data.name == product.name
    assert product_data.price == product.price
    assert product_data.stock == product.stock
    assert product_data.product_rating == product.product_rating
    assert product_data.description == product.description


@pytest.mark.asyncio
async def test_get_product_data_serv_missing_id_not_found_error(db_session):
    with pytest.raises(NotFoundError):
        await get_product_serv(uuid4(), db_session)


@pytest.mark.asyncio
async def test_create_product_review_serv_success(db_session):
    product = product_factory()
    user = user_factory()
    token_data = token_data_factory(user)
    review_data = new_review_data_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    await create_product_review_serv(product.id, review_data, token_data, db_session)

    db_review = (await db_session.execute(select(Review))).scalar_one()
    db_product = (await db_session.execute(select(Product))).scalar_one()
    await db_session.refresh(db_product, attribute_names=["product_rating"])

    assert db_review.product_id == db_product.id
    assert db_review.user_id == user.id
    assert db_review.text == review_data.text
    assert db_product.product_rating.rating_count == 1
    assert db_product.product_rating.avg_rating == review_data.product_rating


@pytest.mark.asyncio
async def test_create_product_review_serv_missing_product_id_not_found_error(
    db_session,
):
    user = user_factory()
    token_data = token_data_factory(user)
    review_data = new_review_data_factory()
    db_session.add(user)
    await db_session.flush()

    with pytest.raises(NotFoundError):
        await create_product_review_serv(uuid4(), review_data, token_data, db_session)


@pytest.mark.asyncio
async def test_create_product_review_serv_duplicate_review_conflict_error(db_session):
    product = product_factory()
    user = user_factory()
    token_data = token_data_factory(user)
    review_data = new_review_data_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    await create_product_review_serv(product.id, review_data, token_data, db_session)
    await db_session.flush()

    with pytest.raises(ConflictError):
        await create_product_review_serv(
            product.id, review_data, token_data, db_session
        )
        await db_session.flush()
