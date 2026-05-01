from uuid import uuid4

import pytest
from fastapi import status
from sqlalchemy import select

from app.api.dependencies import get_session, get_token_data
from app.database.models.product import Product
from app.database.models.review import Review
from tests.factories.products import (
    new_product_data_factory,
    product_factory,
    product_update_data_factory,
)
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import token_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_product_handler_success(
    db_session, async_client, app, override_get_session
):
    token_data = token_data_factory(user_factory(role="admin"))
    new_product_data = new_product_data_factory(name=" product_name ")

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.post(
        "/api/v1/products/", json=new_product_data.model_dump(mode="json")
    )

    assert response.status_code == status.HTTP_200_OK
    new_product_id = response.json()["id"]
    db_product = await db_session.get(Product, new_product_id)
    assert db_product.name == new_product_data.name.strip()
    assert db_product.price == new_product_data.price
    assert db_product.stock == new_product_data.stock


@pytest.mark.asyncio
async def test_create_product_handler_duplicate_name_conflict_error(
    db_session, async_client, app, override_get_session
):
    product = product_factory(name="product_name")
    db_session.add(product)
    await db_session.flush()

    token_data = token_data_factory(user_factory(role="admin"))
    new_product_data = new_product_data_factory(name=" product_name ")

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.post(
        "/api/v1/products/", json=new_product_data.model_dump(mode="json")
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_get_product_handler_success(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get(f"/api/v1/products/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(product.id)
    assert data["name"] == product.name
    assert data["price"] == product.price
    assert data["stock"] == product.stock


@pytest.mark.asyncio
async def test_get_product_handler_missing_id_not_found_error(
    async_client, app, override_get_session
):
    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get(f"/api/v1/products/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_product_handler_success(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    token_data = token_data_factory(user_factory(role="admin"))
    product_update_data = product_update_data_factory()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.patch(
        f"/api/v1/products/{product.id}",
        json=product_update_data.model_dump(mode="json"),
    )

    assert response.status_code == status.HTTP_200_OK
    db_session.expunge_all()
    db_product = await db_session.get(Product, product.id)
    assert db_product.name == product_update_data.name.strip()
    assert db_product.price == product_update_data.price
    assert db_product.stock == product_update_data.stock


@pytest.mark.asyncio
async def test_update_product_handler_no_data_bad_request_error(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    token_data = token_data_factory(user_factory(role="admin"))
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.patch(f"/api/v1/products/{product.id}", json={})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_product_handler_duplicate_name_conflict_error(
    db_session, async_client, app, override_get_session
):
    product1 = product_factory(name="name1")
    product2 = product_factory(name="name2")
    db_session.add_all([product1, product2])
    await db_session.flush()

    token_data = token_data_factory(user_factory(role="admin"))
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.patch(
        f"/api/v1/products/{product2.id}", json={"name": "name1"}
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_update_product_handler_missing_product_id_not_found_error(
    async_client, app, override_get_session
):
    token_data = token_data_factory(user_factory(role="admin"))
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.patch(
        f"/api/v1/products/{uuid4()}", json={"name": "new"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_product_handler_success(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    token_data = token_data_factory(user=user_factory(role="admin"))
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.delete(f"/api/v1/products/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    db_session.expunge_all()
    db_product = await db_session.get(Product, product.id)
    assert db_product is None


@pytest.mark.asyncio
async def test_delete_product_handler_missing_id_not_found_error(
    async_client, app, override_get_session
):
    token_data = token_data_factory(user_factory(role="admin"))
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.delete(f"/api/v1/products/{uuid4()}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_review_handler_success(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    user = user_factory()
    token_data = token_data_factory(user)
    new_review_data = new_review_data_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.post(
        f"/api/v1/products/{product.id}/reviews",
        json=new_review_data.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == product.id
    assert review.user_id == user.id
    assert review.text == new_review_data.text


@pytest.mark.asyncio
async def test_create_review_handler_missing_product_id_not_found_error(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    token_data = token_data_factory(user)
    new_review_data = new_review_data_factory()
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.post(
        f"/api/v1/products/{uuid4()}/reviews",
        json=new_review_data.model_dump(),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    review = (await db_session.execute(select(Review))).scalar_one_or_none()
    assert review is None


@pytest.mark.asyncio
async def test_create_review_handler_duplicate_review_conflict_error(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    user = user_factory()
    token_data = token_data_factory(user)
    new_review_data = new_review_data_factory()
    db_session.add_all([user, product])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: token_data

    response = await async_client.post(
        f"/api/v1/products/{product.id}/reviews",
        json=new_review_data.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK

    response = await async_client.post(
        f"/api/v1/products/{product.id}/reviews",
        json=new_review_data.model_dump(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == product.id
    assert review.user_id == user.id
    assert review.text == new_review_data.text
