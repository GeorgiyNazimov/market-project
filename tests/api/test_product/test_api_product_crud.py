import pytest
from fastapi import status
from sqlalchemy import select

from app.database.connection.session import get_session
from app.database.models.product import Product
from tests.factories.products import new_product_data_factory, product_factory


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
