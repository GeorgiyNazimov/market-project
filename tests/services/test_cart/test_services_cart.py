import pytest
from sqlalchemy import select

from app.database.models.cart import Cart
from app.services.cart import delete_cart
from tests.factories.cart import cart_factory
from tests.factories.users import user_factory

@pytest.mark.asyncio
async def test_delete_cart(db_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    await delete_cart(user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None

@pytest.mark.asyncio
async def test_delete_cart_multiple_times(db_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    await db_session.flush()

    await delete_cart(user, db_session)
    await delete_cart(user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one_or_none()
    assert cart is None
