from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.review import Review
from app.repositories.review import (
    create_review_repo,
    delete_review_repo,
    get_review_by_id_repo,
    get_review_by_user_and_product_repo,
    update_review_repo,
)
from tests.factories.products import product_factory
from tests.factories.reviews import (
    new_review_data_factory,
    review_factory,
    review_update_data_factory,
)
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_product_review_repo_success(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    review_data = new_review_data_factory()
    review = Review(
        text=review_data.text,
        product_rating=review_data.product_rating,
        product_id=product.id,
        user_id=user.id,
    )
    await create_review_repo(review, db_session)

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == product.id
    assert review.user_id == user.id
    assert review.text == review_data.text


@pytest.mark.parametrize("missing_entity", ["product", "user"])
@pytest.mark.asyncio
async def test_create_product_review_repo_fk_violation(db_session, missing_entity):
    product = product_factory()
    user = user_factory()

    if missing_entity == "user":
        db_session.add(product)
    else:
        db_session.add(user)

    await db_session.flush()

    review_data = new_review_data_factory()
    review = Review(
        text=review_data.text,
        product_rating=review_data.product_rating,
        product_id=product.id,
        user_id=user.id,
    )
    with pytest.raises(IntegrityError):
        await create_review_repo(review, db_session)
        await db_session.flush()


@pytest.mark.asyncio
async def test_get_review_by_id_repo_success(db_session):
    product = product_factory()
    user = user_factory()
    review = review_factory(product=product, user=user)
    db_session.add_all([user, product, review])
    await db_session.flush()

    db_session.expunge_all()

    db_review = await get_review_by_id_repo(review.id, db_session)

    assert db_review.user_id == review.user_id
    assert db_review.product_id == review.product_id


@pytest.mark.asyncio
async def test_get_review_by_id_repo_missing_id_returns_none(db_session):
    product = product_factory()
    user = user_factory()
    review = review_factory(product=product, user=user)
    db_session.add_all([user, product, review])
    await db_session.flush()

    db_session.expunge_all()

    db_review = await get_review_by_id_repo(uuid4(), db_session)

    assert db_review is None


@pytest.mark.asyncio
async def test_get_review_by_user_and_product_repo_single_review_success(db_session):
    product = product_factory()
    user = user_factory()
    review = review_factory(product=product, user=user)
    db_session.add_all([user, product, review])
    await db_session.flush()

    db_session.expunge_all()

    db_reviews = await get_review_by_user_and_product_repo(
        product.id, user.id, db_session
    )

    assert len(db_reviews) == 1
    assert db_reviews[0].user_id == review.user_id
    assert db_reviews[0].product_id == review.product_id


@pytest.mark.asyncio
async def test_get_review_by_user_and_product_repo_empty_success(db_session):
    product = product_factory()
    user = user_factory()
    review = review_factory(user=user)
    db_session.add_all([user, product, review])
    await db_session.flush()

    db_session.expunge_all()

    db_review = await get_review_by_user_and_product_repo(
        product.id, user.id, db_session
    )

    assert len(db_review) == 0


@pytest.mark.asyncio
async def test_get_review_by_user_and_product_repo_multiple_reviews_success(db_session):
    product = product_factory()
    user = user_factory()
    reviews = [review_factory(product=product, user=user) for _ in range(3)]
    review_ids = [r.id for r in reviews]
    db_session.add_all([user, product, *reviews])
    await db_session.flush()

    db_session.expunge_all()

    db_reviews = await get_review_by_user_and_product_repo(
        product.id, user.id, db_session
    )

    for i in range(3):
        assert db_reviews[i].id in review_ids


@pytest.mark.asyncio
async def test_update_review_repo_no_user_filter_success(db_session):
    user = user_factory()
    review = review_factory(user=user, rating=2)
    update_data = review_update_data_factory(new_rating=5)
    db_session.add_all([user, review])
    await db_session.flush()

    new_rating = 5
    update_data = update_data.model_dump(exclude_unset=True)
    updated_review = await update_review_repo(
        review_id=review.id,
        user_id=None,
        update_data=update_data,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert updated_review.id == db_review.id
    assert db_review.product_rating == new_rating


@pytest.mark.asyncio
async def test_update_review_repo_with_user_filter_success(db_session):
    user = user_factory()
    review = review_factory(user=user, rating=2)
    update_data = review_update_data_factory(new_rating=5)
    db_session.add_all([user, review])
    await db_session.flush()

    new_rating = 5
    update_data = update_data.model_dump(exclude_unset=True)
    updated_review = await update_review_repo(
        review_id=review.id,
        user_id=user.id,
        update_data=update_data,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert updated_review.id == review.id
    assert db_review.product_rating == new_rating


@pytest.mark.asyncio
async def test_update_review_repo_with_wrong_user_returns_none(db_session):
    user = user_factory()
    review = review_factory(user=user, rating=2)
    update_data = review_update_data_factory(new_rating=5)
    db_session.add_all([user, review])
    await db_session.flush()

    old_rating = 2
    update_data = update_data.model_dump(exclude_unset=True)
    updated_review = await update_review_repo(
        review_id=review.id,
        user_id=uuid4(),
        update_data=update_data,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert updated_review is None
    assert db_review.product_rating == old_rating


@pytest.mark.asyncio
async def test_update_review_repo_with_missing_id_returns_none(db_session):
    user = user_factory()
    review = review_factory(user=user, rating=2)
    update_data = review_update_data_factory(new_rating=5)
    db_session.add_all([user, review])
    await db_session.flush()

    old_rating = 2
    update_data = update_data.model_dump(exclude_unset=True)
    updated_review = await update_review_repo(
        review_id=uuid4(),
        user_id=None,
        update_data=update_data,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert updated_review is None
    assert db_review.product_rating == old_rating


@pytest.mark.asyncio
async def test_delete_review_repo_no_user_filter_success(db_session):
    user = user_factory()
    review = review_factory(user=user)
    db_session.add_all([user, review])
    await db_session.flush()

    deleted_id = await delete_review_repo(
        review_id=review.id,
        user_id=None,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert deleted_id == review.id
    assert db_review is None


@pytest.mark.asyncio
async def test_delete_review_repo_with_user_filter_success(db_session):
    user = user_factory()
    review = review_factory(user=user)
    db_session.add_all([user, review])
    await db_session.flush()

    deleted_id = await delete_review_repo(
        review_id=review.id,
        user_id=user.id,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert deleted_id == review.id
    assert db_review is None


@pytest.mark.asyncio
async def test_delete_review_repo_with_wrong_user_returns_none(db_session):
    user = user_factory()
    review = review_factory(user=user)
    db_session.add_all([user, review])
    await db_session.flush()

    deleted_id = await delete_review_repo(
        review_id=review.id,
        user_id=uuid4(),
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert deleted_id is None
    assert db_review is not None


@pytest.mark.asyncio
async def test_delete_review_repo_with_missing_id_returns_none(db_session):
    user = user_factory()
    review = review_factory(user=user)
    db_session.add_all([user, review])
    await db_session.flush()

    deleted_id = await delete_review_repo(
        review_id=uuid4(),
        user_id=None,
        session=db_session,
    )

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)

    assert deleted_id is None
    assert db_review is not None
