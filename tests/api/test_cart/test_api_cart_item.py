import pytest
from fastapi import status
from sqlalchemy import select

from app.api.dependencies import get_session, get_token_data
from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from tests.factories.cart import (
    cart_factory,
    cart_item_factory,
    update_cart_item_data_factory,
)
from tests.factories.products import product_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_delete_cart_item_success(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    cart = cart_factory(user)
    cart_item = cart_item_factory(cart)
    db_session.add_all([user, cart, cart_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.delete(
        f"/api/v1/carts/delete_cart_item/{cart_item.id}"
    )

    assert response.status_code == status.HTTP_200_OK

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert db_cart_item is None


@pytest.mark.asyncio
async def test_delete_cart_item_other_user_forbidden_error(
    db_session, async_client, app, override_get_session
):
    my_user = user_factory()
    other_cart_item = cart_item_factory()
    db_session.add_all([my_user, other_cart_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: my_user

    response = await async_client.delete(
        f"/api/v1/carts/delete_cart_item/{other_cart_item.id}"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item == other_cart_item


@pytest.mark.asyncio
async def test_get_cart_items_success(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    cart = cart_factory(user)
    cart_items = [cart_item_factory(cart) for _ in range(3)]
    cart_item_ids = [str(item.id) for item in cart_items]
    db_session.add_all([user, cart, *cart_items])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.get("/api/v1/carts/")

    assert response.status_code == status.HTTP_200_OK
    db_cart_items = response.json()

    for db_item in db_cart_items["cart_items"]:
        assert db_item["id"] in cart_item_ids


@pytest.mark.asyncio
async def test_get_cart_items_other_user_forbidden_error(
    db_session, async_client, app, override_get_session
):
    my_user = user_factory()
    other_user = user_factory()
    other_cart = cart_factory(other_user)
    other_cart_items = [cart_item_factory(other_cart) for _ in range(3)]
    db_session.add_all([my_user, other_user, other_cart, *other_cart_items])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: my_user

    response = await async_client.get(f"/api/v1/carts/?target_user_id={other_user.id}")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_cart_items_admin_can_view_any(
    db_session, async_client, app, override_get_session
):
    admin_user = user_factory(role="admin")
    other_user = user_factory()
    other_cart = cart_factory(other_user)
    other_cart_items = [cart_item_factory(other_cart) for _ in range(3)]
    cart_item_ids = [str(item.id) for item in other_cart_items]
    db_session.add_all([admin_user, other_user, other_cart, *other_cart_items])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: admin_user

    response = await async_client.get(f"/api/v1/carts/?target_user_id={other_user.id}")

    assert response.status_code == status.HTTP_200_OK
    db_cart_items = response.json()

    for db_item in db_cart_items["cart_items"]:
        assert db_item["id"] in cart_item_ids


@pytest.mark.asyncio
async def test_create_cart_item_success(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.post(f"/api/v1/carts/create_cart_item/{product.id}")

    assert response.status_code == status.HTTP_200_OK
    db_cart_item = response.json()
    db_cart = (await db_session.execute(select(Cart))).scalar_one()
    assert db_cart_item["product_id"] == str(product.id)
    assert db_cart_item["cart_id"] == str(db_cart.id)


@pytest.mark.asyncio
async def test_create_cart_item_same_product_multiple_times_conflict_error(
    db_session, async_client, app, override_get_session
):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.post(f"/api/v1/carts/create_cart_item/{product.id}")
    assert response.status_code == status.HTTP_200_OK

    response = await async_client.post(f"/api/v1/carts/create_cart_item/{product.id}")
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_update_cart_item_quantity_success(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    cart = cart_factory(user)
    cart_item = cart_item_factory(cart)
    db_session.add_all([user, cart, cart_item])
    await db_session.flush()
    update_cart_item_data = update_cart_item_data_factory(cart_item.id, new_quantity=5)
    update_cart_item_data.cart_item_id = str(update_cart_item_data.cart_item_id)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.patch(
        "/api/v1/carts/update_cart_item", json=update_cart_item_data.model_dump()
    )

    assert response.status_code == status.HTTP_200_OK
    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item.id == cart_item.id
    assert db_cart_item.quantity == update_cart_item_data.new_quantity


@pytest.mark.asyncio
async def test_update_cart_item_quantity_other_user_forbidden_error(
    db_session, async_client, app, override_get_session
):
    my_user = user_factory()
    other_cart_item = cart_item_factory()
    db_session.add_all([my_user, other_cart_item])
    await db_session.flush()
    update_cart_item_data = update_cart_item_data_factory(
        other_cart_item.id, new_quantity=5
    )
    update_cart_item_data.cart_item_id = str(update_cart_item_data.cart_item_id)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: my_user

    response = await async_client.patch(
        "/api/v1/carts/update_cart_item", json=update_cart_item_data.model_dump()
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item.id == other_cart_item.id
    assert db_cart_item.quantity == other_cart_item.quantity
