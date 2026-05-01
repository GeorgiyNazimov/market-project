from datetime import datetime, timedelta

import pytest
from fastapi import status

from app.api.dependencies import get_session
from tests.factories.products import multiple_products_factory, product_factory
from tests.factories.reviews import review_factory


@pytest.mark.asyncio
async def test_get_product_list_handler_without_cursor_success(
    async_client, db_session, override_get_session, app
):
    products = multiple_products_factory(6)
    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(products)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    limit = 2
    response = await async_client.get(f"/api/v1/products/", params={"limit": limit})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["product_list"]) == limit
    for i in range(limit):
        assert data["product_list"][i]["id"] == str(products[i].id)


@pytest.mark.asyncio
async def test_get_product_list_handler_pagination_success(
    async_client, db_session, override_get_session, app
):
    products = multiple_products_factory(6)
    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(products)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    limit = 2
    first_resp = await async_client.get("/api/v1/products/", params={"limit": limit})
    cursor = first_resp.json()["next_cursor"]

    response = await async_client.get(
        "/api/v1/products/", params={"limit": limit, "cursor": cursor}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["product_list"]) == limit
    for i in range(limit):
        assert data["product_list"][i]["id"] == str(products[i + limit].id)


@pytest.mark.asyncio
async def test_get_product_list_handler_unsupported_sort_field_bad_request_error(
    async_client, db_session, override_get_session, app
):
    products = multiple_products_factory(6)
    products.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    db_session.add_all(products)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    limit = 2
    response = await async_client.get(
        f"/api/v1/products/", params={"limit": limit, "sort_by": "random"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_get_product_review_list_handler_without_cursor_success(
    async_client, db_session, override_get_session, app
):
    product = product_factory()
    reviews = [
        review_factory(
            product=product, created_at=datetime.utcnow() + timedelta(minutes=i)
        )
        for i in range(6)
    ]
    db_session.add_all([product, *reviews])
    await db_session.flush()

    reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    app.dependency_overrides[get_session] = override_get_session

    limit = 2
    response = await async_client.get(
        f"/api/v1/products/{product.id}/reviews",
        params={"limit": limit, "sort_by": "created_at"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["review_list"]) == limit
    for i in range(limit):
        assert data["review_list"][i]["id"] == str(reviews[i].id)
        assert data["review_list"][i]["user"]["first_name"] is not None


@pytest.mark.asyncio
async def test_get_product_review_list_handler_pagination_success(
    async_client, db_session, override_get_session, app
):
    product = product_factory()
    reviews = [
        review_factory(
            product=product, created_at=datetime.utcnow() + timedelta(minutes=i)
        )
        for i in range(6)
    ]
    db_session.add_all([product, *reviews])
    await db_session.flush()

    reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    app.dependency_overrides[get_session] = override_get_session

    limit = 2
    response = await async_client.get(
        f"/api/v1/products/{product.id}/reviews",
        params={"limit": limit, "sort_by": "created_at"},
    )
    cursor = response.json()["next_cursor"]

    response = await async_client.get(
        f"/api/v1/products/{product.id}/reviews",
        params={"limit": limit, "sort_by": "created_at", "cursor": cursor},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["review_list"]) == limit
    for i in range(limit):
        assert data["review_list"][i]["id"] == str(reviews[i + limit].id)
        assert data["review_list"][i]["user"]["first_name"] is not None


@pytest.mark.asyncio
async def test_get_product_review_list_handler_unsupported_sort_field_bad_request_error(
    async_client, db_session, override_get_session, app
):
    product = product_factory()
    reviews = [
        review_factory(
            product=product, created_at=datetime.utcnow() + timedelta(minutes=i)
        )
        for i in range(6)
    ]
    db_session.add_all([product, *reviews])
    await db_session.flush()

    reviews.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    app.dependency_overrides[get_session] = override_get_session

    limit = 2
    response = await async_client.get(
        f"/api/v1/products/{product.id}/reviews",
        params={"limit": limit, "sort_by": "random"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
