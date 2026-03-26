import pytest
from fastapi import status
from decimal import Decimal
from app.api.dependencies import get_session, RoleChecker, get_token_data
from app.database.models import Product
from tests.factories.users import user_factory
from tests.factories.products import product_factory
from tests.factories.cart import cart_item_factory, cart_factory

@pytest.mark.asyncio
async def test_api_create_order_success(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user=user)
    product = product_factory(stock=10, price=Decimal("100.00"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=2)
    db_session.add_all([user, product, cart, cart_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.post(
        "/api/v1/order/create_order", 
        json={"cart_item_ids": [str(cart_item.id)]}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_price"] == "200.00"
    assert data["items"][0]["product_name"] == product.name

@pytest.mark.asyncio
async def test_api_create_order_admin_access_denied_error(db_session, async_client, app, override_get_session):
    user = user_factory(role="admin")
    cart = cart_factory(user=user)
    product = product_factory(stock=10, price=Decimal("100.00"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=2)
    db_session.add_all([user, cart, product, cart_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.post(
        "/api/v1/order/create_order",
        json={"cart_item_ids": [str(cart_item.id)]}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["message"] == "Not enough permissions"

@pytest.mark.asyncio
async def test_api_create_order_unauthorized_error(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user=user)
    product = product_factory(stock=10, price=Decimal("100.00"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=2)
    db_session.add_all([user, cart, product, cart_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.post(
        "/api/v1/order/create_order",
        json={"cart_item_ids": [str(cart_item.id)]}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_api_create_order_empty_list_error(db_session, async_client, app, override_get_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.post("/api/v1/order/create_order", json={"cart_item_ids": []})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["message"] == "You must choose cart items"

@pytest.mark.asyncio
async def test_api_create_order_foreign_cart_items_error(db_session, async_client, app, override_get_session):
    my_user = user_factory()
    other_user = user_factory()
    my_cart = cart_factory(user=my_user)
    other_cart = cart_factory(user=other_user)
    product = product_factory(stock=10, price=Decimal("100.00"))
    my_cart_item = cart_item_factory(cart=my_cart, product=product, quantity=2)
    other_cart_item = cart_item_factory(cart=other_cart, product=product, quantity=3)
    db_session.add_all([
        my_user,
        other_user,
        my_cart,
        other_cart,
        product,
        my_cart_item,
        other_cart_item,
    ])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: my_user

    response = await async_client.post(
        "/api/v1/order/create_order",
        json={"cart_item_ids": [str(my_cart_item.id), str(other_cart_item.id)]}
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["message"] == "You can only select items from your cart"

@pytest.mark.asyncio
async def test_api_create_order_insufficient_stock_error(db_session, async_client, app, override_get_session):
    user = user_factory()
    cart = cart_factory(user=user)
    product = product_factory(stock=2, price=Decimal("100.00"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=5)
    db_session.add_all([user, cart, product, cart_item])
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.post("/api/v1/order/create_order", json={"cart_item_ids": [str(cart_item.id)]})

    data = response.json()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert data["error"]["message"] == "Insufficient stock"
    assert data["error"]["details"][0]["id"] == str(product.id)
    assert data["error"]["details"][0]["name"] == product.name
    assert data["error"]["details"][0]["requested"] == cart_item.quantity
    assert data["error"]["details"][0]["available"] == product.stock
