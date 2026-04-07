import pytest
from fastapi import status
from sqlalchemy import select

from app.api.dependencies import get_session, get_token_data
from app.database.models.product import Product
from app.database.models.review import Review
from tests.factories.products import new_product_data_factory, product_factory
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_product(db_session, async_client, app, override_get_session):
    new_product_data = new_product_data_factory()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.post(
        "/api/v1/product/trade", json=new_product_data.model_dump()
    )

    assert response.status_code == status.HTTP_200_OK
    product = (await db_session.execute(select(Product))).scalar_one()
    assert product.stock == new_product_data.stock
    assert product.name == new_product_data.name
    assert product.price == new_product_data.price


@pytest.mark.asyncio
async def test_get_product_data(db_session, async_client, app, override_get_session):
    new_product = product_factory()
    db_session.add(new_product)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get(f"/api/v1/product/{new_product.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(new_product.id)
    assert data["name"] == new_product.name
    assert data["price"] == new_product.price


@pytest.mark.asyncio
async def test_create_review(db_session, async_client, app, override_get_session):
    new_product = product_factory()
    new_user = user_factory()
    new_review_data = new_review_data_factory()
    db_session.add_all([new_user, new_product])
    await db_session.flush()

    def override_get_token_data():
        yield new_user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = override_get_token_data

    response = await async_client.post(
        f"/api/v1/product/{new_product.id}/create_review",
        json=new_review_data.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == new_product.id
    assert review.user_id == new_user.id
    assert review.text == new_review_data.text
