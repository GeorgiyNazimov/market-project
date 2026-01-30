import pytest
from fastapi import status
from sqlalchemy import select

from app.database.connection.session import get_session
from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.services.auth import get_current_user
from tests.factories.cart import (
    cart_factory,
    cart_item_factory,
    update_cart_item_data_factory,
)
from tests.factories.products import product_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_delete_cart_item(db_session, async_client, app, override_get_session):
    new_cart_item = cart_item_factory()
    db_session.add(new_cart_item)
    await db_session.flush()
    user = new_cart_item.cart.user

    def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.delete(
        f"/api/v1/cart/delete_cartitem/{new_cart_item.id}"
    )

    assert response.status_code == status.HTTP_200_OK
    cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert cart_item is None


@pytest.mark.asyncio
async def test_get_cart_item(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    new_cart_items = [cart_item_factory(cart) for i in range(4)]
    new_cart_items.sort(key=lambda x: x.id)
    db_session.add_all(new_cart_items)
    await db_session.flush()

    def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.get("/api/v1/cart/")

    assert response.status_code == status.HTTP_200_OK
    cart_items = response.json()
    cart_items["cart_items"].sort(key=lambda x: x["id"])

    assert cart_items["cart_items"][0]["id"] == str(new_cart_items[0].id)
    assert cart_items["cart_items"][1]["id"] == str(new_cart_items[1].id)
    assert cart_items["cart_items"][2]["id"] == str(new_cart_items[2].id)
    assert cart_items["cart_items"][3]["id"] == str(new_cart_items[3].id)


@pytest.mark.asyncio
async def test_insert_cart_item(db_session, async_client, app, override_get_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.post(f"/api/v1/cart/create_cartitem/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    new_cart_item = response.json()
    cart = (await db_session.execute(select(Cart))).scalar_one()
    assert new_cart_item["product_id"] == str(product.id)
    assert new_cart_item["cart_id"] == str(cart.id)


@pytest.mark.asyncio
async def test_insert_cart_item_same_product_multiple_times_integrity_error(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    async def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.post(f"/api/v1/cart/create_cartitem/{product.id}")
    assert response.status_code == status.HTTP_200_OK

    response = await async_client.post(f"/api/v1/cart/create_cartitem/{product.id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_update_cart_item(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user)
    new_cart_item = cart_item_factory(cart)
    db_session.add(new_cart_item)
    await db_session.flush()
    update_cart_item_data = update_cart_item_data_factory(
        new_cart_item.id, new_quantity=5
    )
    update_cart_item_data.cart_item_id = str(update_cart_item_data.cart_item_id)

    def override_get_current_user():
        yield user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.patch(
        "/api/v1/cart/update_cartitem", json=update_cart_item_data.model_dump()
    )

    assert response.status_code == status.HTTP_200_OK
    cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert cart_item.quantity == update_cart_item_data.new_quantity
