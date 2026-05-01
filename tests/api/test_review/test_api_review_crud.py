from uuid import uuid4

import pytest
from fastapi import status
from sqlalchemy import select

from app.api.dependencies import get_session, get_token_data
from app.database.models.product import Product
from app.database.models.review import Review
from tests.factories.products import product_factory
from tests.factories.reviews import (
    new_review_data_factory,
    review_factory,
    review_update_data_factory,
)
from tests.factories.users import token_data_factory, user_factory


@pytest.mark.asyncio
async def test_update_review_handler_success(
    db_session, async_client, app, override_get_session
):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    token_data = token_data_factory(user=review.user)
    update_data = review_update_data_factory(new_rating=1)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.patch(
        f"/api/v1/reviews/{review.id}", json=update_data.model_dump()
    )

    assert response.status_code == status.HTTP_200_OK
    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)
    db_product = await db_session.get(Product, review.product_id)
    await db_session.refresh(db_product, attribute_names=["product_rating"])

    assert db_review.product_rating == 1
    assert db_review.text == update_data.text
    assert db_product.product_rating.avg_rating == 1


@pytest.mark.asyncio
async def test_update_review_handler_admin_success(
    db_session, async_client, app, override_get_session
):
    review = review_factory(rating=2)
    db_session.add(review)
    await db_session.flush()

    admin_token = token_data_factory(user_factory(role="admin"))
    update_data = review_update_data_factory(new_rating=5, text="Admin edit")
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: admin_token

    response = await async_client.patch(
        f"/api/v1/reviews/{review.id}", json=update_data.model_dump()
    )

    assert response.status_code == status.HTTP_200_OK

    db_session.expunge_all()
    db_review = await db_session.get(Review, review.id)
    assert db_review.product_rating == 5
    assert db_review.text == "Admin edit"


@pytest.mark.asyncio
async def test_update_review_handler_no_data_bad_request_error(
    db_session, async_client, app, override_get_session
):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data_factory(review.user)

    response = await async_client.patch(f"/api/v1/reviews/{review.id}", json={})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_review_handler_wrong_user_not_found_error(
    db_session, async_client, app, override_get_session
):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data_factory(
        user_factory()
    )

    response = await async_client.patch(
        f"/api/v1/reviews/{review.id}", json={"text": "new"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_review_handler_success(
    db_session, async_client, app, override_get_session
):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data_factory(review.user)

    response = await async_client.delete(f"/api/v1/reviews/{review.id}")

    assert response.status_code == status.HTTP_200_OK
    db_session.expunge_all()
    assert await db_session.get(Review, review.id) is None
    db_product = await db_session.get(Product, review.product_id)
    await db_session.refresh(db_product, attribute_names=["product_rating"])
    assert db_product.product_rating.rating_count == 0


@pytest.mark.asyncio
async def test_delete_review_handler_admin_success(
    db_session, async_client, app, override_get_session
):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data_factory(
        user_factory(role="admin")
    )

    response = await async_client.delete(f"/api/v1/reviews/{review.id}")
    assert response.status_code == status.HTTP_200_OK
    db_session.expunge_all()
    assert await db_session.get(Review, review.id) is None


@pytest.mark.asyncio
async def test_delete_review_handler_wrong_user_not_found_error(
    db_session, async_client, app, override_get_session
):
    review = review_factory()
    db_session.add(review)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data_factory(
        user_factory()
    )

    response = await async_client.delete(f"/api/v1/reviews/{review.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
