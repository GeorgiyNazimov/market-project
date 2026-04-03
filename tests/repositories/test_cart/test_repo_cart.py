import pytest
from sqlalchemy import select

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.repositories.cart import delete_cart_repo, get_cart_repo
from tests.factories.cart import cart_factory, cart_item_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_delete_cart_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_items = [cart_item_factory(cart) for _ in range(3)]
    db_session.add_all([user, cart, *cart_items])
    await db_session.flush()

    await delete_cart_repo(user.id, db_session)

    db_cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    db_cart_items = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert db_cart is None
    assert db_cart_items is None


@pytest.mark.asyncio
async def test_delete_cart_multiple_times_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    await delete_cart_repo(user.id, db_session)
    await delete_cart_repo(user.id, db_session)

    db_cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert db_cart is None


@pytest.mark.asyncio
async def test_get_cart_success(db_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    await get_cart_repo(user.id, db_session)

    db_cart = (await db_session.execute(select(Cart))).scalar_one()
    assert db_cart.user_id == user.id


@pytest.mark.asyncio
async def test_get_cart_multiple_time_return_same_cart(db_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    cart1 = await get_cart_repo(user.id, db_session)
    cart2 = await get_cart_repo(user.id, db_session)

    assert cart1.user_id == user.id
    assert cart2.id == cart1.id
