import pytest
from fastapi import status
from sqlalchemy import select

from app.api.dependencies import get_session, get_token_data
from app.database.models.cart import Cart
from tests.factories.cart import cart_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_delete_cart_success(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.delete("/api/v1/carts/delete_my_cart")

    assert response.status_code == status.HTTP_200_OK
    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None


@pytest.mark.asyncio
async def test_delete_cart_multiple_times_success(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.delete("/api/v1/carts/delete_my_cart")
    assert response.status_code == status.HTTP_200_OK
    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None

    response = await async_client.delete("/api/v1/carts/delete_my_cart")
    assert response.status_code == status.HTTP_200_OK
