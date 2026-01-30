import pytest
from sqlalchemy import select
from fastapi import status

from app.database.connection.session import get_session
from app.database.models.cart import Cart
from app.services.auth import get_current_user
from tests.factories.cart import cart_factory
from tests.factories.users import user_factory

@pytest.mark.asyncio
async def test_delete_cart(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.delete("/api/v1/cart/delete_my_cart")

    assert response.status_code == status.HTTP_200_OK
    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None

@pytest.mark.asyncio
async def test_delete_cart_multiple_times(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.delete("/api/v1/cart/delete_my_cart")
    assert response.status_code == status.HTTP_200_OK
    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None
    
    response = await async_client.delete("/api/v1/cart/delete_my_cart")
    assert response.status_code == status.HTTP_200_OK