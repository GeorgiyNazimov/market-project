from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.exceptions import BadRequest, ConflictError, NotFoundError
from app.database.models.product import Product
from app.database.models.review import Review
from app.schemas.review import ReviewUpdateData
from app.services.review import (
    create_review_serv,
    delete_review_serv,
    update_review_serv,
)
from tests.factories.products import product_factory
from tests.factories.reviews import (
    new_review_data_factory,
    review_factory,
    review_update_data_factory,
)
from tests.factories.users import token_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_product_review_serv_success(db_session):
    product = product_factory()
    user = user_factory()
    token_data = token_data_factory(user)
    review_data = new_review_data_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    await create_review_serv(product.id, review_data, token_data, db_session)

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
        await create_review_serv(uuid4(), review_data, token_data, db_session)


@pytest.mark.asyncio
async def test_create_product_review_serv_duplicate_review_conflict_error(db_session):
    product = product_factory()
    user = user_factory()
    review = review_factory(user=user, product=product)
    db_session.add_all([user, product, review])
    await db_session.flush()

    token_data = token_data_factory(user)
    review_data = new_review_data_factory()

    with pytest.raises(ConflictError):
        await create_review_serv(product.id, review_data, token_data, db_session)


@pytest.mark.asyncio
async def test_update_review_serv_success(db_session):
    review = review_factory(rating=5)
    db_session.add(review)
    await db_session.flush()

    token_data = token_data_factory(user=review.user)
    update_data = review_update_data_factory(new_rating=1)

    updated_id = await update_review_serv(
        review.id, update_data, token_data, db_session
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, updated_id)
    db_product = await db_session.get(Product, review.product_id)
    await db_session.refresh(db_product, attribute_names=["product_rating"])

    assert updated_id == review.id
    assert db_review.product_rating == 1
    assert db_review.text == update_data.text
    assert db_product.product_rating.avg_rating == 1
    assert db_product.product_rating.rating_1_count == 1
    assert db_product.product_rating.rating_5_count == 0
    assert db_product.product_rating.rating_count == 1


@pytest.mark.asyncio
async def test_update_review_serv_admin_success(db_session):
    review = review_factory(rating=2)
    db_session.add(review)
    await db_session.flush()

    admin_token = token_data_factory(user_factory(role="admin"))
    update_data = review_update_data_factory(new_rating=5)

    updated_id = await update_review_serv(
        review.id, update_data, admin_token, db_session
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, updated_id)

    assert updated_id == review.id
    assert db_review.product_rating == 5


@pytest.mark.asyncio
async def test_update_review_serv_no_data_bad_request_error(db_session):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    token_data = token_data_factory(user=review.user)
    update_data = ReviewUpdateData()

    with pytest.raises(BadRequest):
        await update_review_serv(review.id, update_data, token_data, db_session)


@pytest.mark.asyncio
async def test_update_review_serv_missing_id_not_found_error(db_session):
    token_data = token_data_factory()
    update_data = review_update_data_factory()

    with pytest.raises(NotFoundError):
        await update_review_serv(uuid4(), update_data, token_data, db_session)


@pytest.mark.asyncio
async def test_update_review_serv_wrong_user_not_found_error(db_session):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    token_data = token_data_factory()
    update_data = review_update_data_factory()

    with pytest.raises(NotFoundError):
        await update_review_serv(review.id, update_data, token_data, db_session)


@pytest.mark.asyncio
async def test_delete_review_serv_success(db_session):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    token_data = token_data_factory(user=review.user)

    deleted_id = await delete_review_serv(review.id, token_data, db_session)

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)
    db_product = await db_session.get(Product, review.product_id)
    await db_session.refresh(db_product, attribute_names=["product_rating"])

    assert db_review is None
    assert deleted_id == review.id
    assert db_product.product_rating.avg_rating == 0
    assert db_product.product_rating.rating_count == 0


@pytest.mark.asyncio
async def test_delete_review_serv_admin_success(db_session):
    user = user_factory(role="admin")
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    token_data = token_data_factory(user=user)

    deleted_id = await delete_review_serv(review.id, token_data, db_session)

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert db_review is None
    assert deleted_id == review.id


@pytest.mark.asyncio
async def test_delete_review_serv_missing_id_not_found_error(db_session):
    token_data = token_data_factory()

    with pytest.raises(NotFoundError):
        await delete_review_serv(uuid4(), token_data, db_session)


@pytest.mark.asyncio
async def test_delete_review_serv_wrong_user_not_found_error(db_session):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()
    token_data = token_data_factory()

    with pytest.raises(NotFoundError):
        await delete_review_serv(review.id, token_data, db_session)
