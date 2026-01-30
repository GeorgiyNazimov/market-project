import pytest
from sqlalchemy import select

from app.database.models.cart import Cart
from app.repositories.cart import delete_cart_from_db, get_cart
from tests.factories.cart import cart_factory
from tests.factories.users import user_factory

@pytest.mark.asyncio
async def test_delete_cart(db_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    await delete_cart_from_db(user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None

@pytest.mark.asyncio
async def test_delete_cart_multiple_times(db_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    await delete_cart_from_db(user, db_session)
    await delete_cart_from_db(user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None

@pytest.mark.asyncio
async def test_get_cart(db_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    await get_cart(user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one()
    assert cart.user_id == user.id

@pytest.mark.asyncio
async def test_get_cart_multiple_time_return_same_cart(db_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    cart1 = await get_cart(user, db_session)
    cart2 = await get_cart(user, db_session)

    assert cart1.user_id == user.id
    assert cart2.id == cart1.id