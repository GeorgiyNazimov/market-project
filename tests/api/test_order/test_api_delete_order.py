import pytest
from fastapi import status
from decimal import Decimal
from app.api.dependencies import get_session, RoleChecker, get_token_data
from app.database.models import Product
from tests.factories.users import user_factory
from tests.factories.products import product_factory
from tests.factories.orders import order_factory, order_item_factory

@pytest.mark.asyncio
async def test_api_delete_order_success(db_session, async_client, app, override_get_session):
    user = user_factory()
    product = product_factory(stock=5)
    order = order_factory(user=user)
    order_item = order_item_factory(order=order, product=product, quantity=2)
    db_session.add_all([user, product, order, order_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.delete(f"/api/v1/order/delete_order/{order.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "Successful delete"

@pytest.mark.asyncio
async def test_api_delete_order_unauthorized_error(db_session, async_client, app, override_get_session):
    user = user_factory()
    product = product_factory(stock=5)
    order = order_factory(user=user)
    order_item = order_item_factory(order=order, product=product, quantity=2)
    db_session.add_all([user, product, order, order_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.delete(f"/api/v1/order/delete_order/{order.id}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_api_delete_order_foreign_user_id_error(db_session, async_client, app, override_get_session):
    my_user = user_factory()
    other_order = order_factory()
    product = product_factory(stock=5)
    other_order_item = order_item_factory(order=other_order, product=product, quantity=5)
    db_session.add_all([
        my_user,
        other_order,
        product,
        other_order_item,
    ])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: my_user

    response = await async_client.delete(f"/api/v1/order/delete_order/{other_order.id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["error"]["message"] == "Order not found or access denied"

@pytest.mark.asyncio
async def test_api_delete_order_admin_access_success(db_session, async_client, app, override_get_session):
    admin = user_factory(role="admin")
    user = user_factory()
    product = product_factory(stock=5)
    order = order_factory(user=user)
    order_item = order_item_factory(order=order, product=product, quantity=2)
    db_session.add_all([admin, user, product, order, order_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: admin

    response = await async_client.delete(f"/api/v1/order/delete_order/{order.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "Successful delete"
