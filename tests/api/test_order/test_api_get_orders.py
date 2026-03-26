import pytest
from fastapi import status
from app.api.dependencies import get_session, RoleChecker, get_token_data
from tests.factories.users import user_factory
from tests.factories.orders import order_factory


@pytest.mark.asyncio
async def test_api_get_orders_list_success(db_session, async_client, app, override_get_session):
    user = user_factory()
    order = order_factory(user=user)
    db_session.add_all([user, order])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.get("/api/v1/order/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["orders"]) == 1
    assert data["orders"][0]["id"] == str(order.id)

@pytest.mark.asyncio
async def test_api_get_orders_list_unauthorized_error(db_session, async_client, app, override_get_session):
    user = user_factory()
    order = order_factory(user=user)
    db_session.add_all([user, order])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get("/api/v1/order/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_api_get_orders_list_foreign_user_id_error(db_session, async_client, app, override_get_session):
    my_user = user_factory()
    other_user = user_factory()
    my_order = order_factory(user=my_user)
    other_order = order_factory(user=other_user)
    db_session.add_all([my_user, other_user, my_order, other_order])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: my_user

    response = await async_client.get(f"/api/v1/order/?target_user_id={other_user.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["message"] == "You can only view your own orders"

@pytest.mark.asyncio
async def test_api_get_orders_list_admin_access_success(db_session, async_client, app, override_get_session):
    admin = user_factory(role="admin")
    user = user_factory()
    order = order_factory(user=user)
    db_session.add_all([admin, user, order])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: admin

    response = await async_client.get(f"/api/v1/order/?target_user_id={user.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["orders"]) == 1
    assert data["orders"][0]["id"] == str(order.id)