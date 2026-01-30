import pytest
from fastapi import status

from app.database.connection import get_session
from tests.factories.products import multiple_products_factory


@pytest.mark.asyncio
async def test_get_product_list_without_cursor(
    async_client, db_session, override_get_session, app
):
    products = multiple_products_factory(5)
    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(products)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get("/api/v1/product/?limit=2")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["product_list"]) == 2
    assert data["product_list"][0]["id"] == str(products[0].id)


@pytest.mark.asyncio
async def test_get_product_list_with_cursor(
    async_client, db_session, override_get_session, app
):
    products = multiple_products_factory(5)
    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(products)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get("/api/v1/product/?limit=2")
    data = response.json()
    next_cursor = data["next_cursor"]
    created_at_cursor = next_cursor["created_at"]
    id_cursor = next_cursor["id"]
    response = await async_client.get(
        f"/api/v1/product/?limit=2&created_at_cursor={created_at_cursor}&id_cursor={id_cursor}"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["product_list"]) == 2
    assert data["product_list"][0]["id"] == str(products[2].id)
