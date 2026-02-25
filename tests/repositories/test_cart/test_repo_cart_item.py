import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.repositories.cart import (
    delete_cart_item_from_db,
    get_cart_items_from_db,
    insert_cart_item,
    update_cart_item_quantity_in_db,
)
from tests.factories.cart import (
    cart_factory,
    cart_item_factory,
    update_cart_item_data_factory,
)
from tests.factories.products import product_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_delete_cart_item(db_session):
    new_cart_item = cart_item_factory()
    db_session.add(new_cart_item)
    await db_session.flush()

    await delete_cart_item_from_db(new_cart_item.id, db_session)

    cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert cart_item is None


@pytest.mark.asyncio
async def test_get_cart_item(db_session):
    user = user_factory()
    cart = cart_factory(user)
    db_session.add_all([user, cart])
    new_cart_items = [cart_item_factory(cart) for i in range(4)]
    new_cart_items.sort(key=lambda x: x.id)
    db_session.add_all(new_cart_items)
    cart.total_items = 4
    await db_session.flush()

    cart_items, total_items = await get_cart_items_from_db(user, db_session)
    cart_items.sort(key=lambda x: x.id)

    assert cart_items[0].id == new_cart_items[0].id
    assert cart_items[1].id == new_cart_items[1].id
    assert cart_items[2].id == new_cart_items[2].id
    assert cart_items[3].id == new_cart_items[3].id
    assert total_items == 4


@pytest.mark.asyncio
async def test_insert_cart_item(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    new_cart_item = await insert_cart_item(product.id, user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one()
    assert new_cart_item.product_id == product.id
    assert new_cart_item.cart_id == cart.id


@pytest.mark.asyncio
async def test_insert_cart_item_same_product_multiple_times_integrity_error(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    await insert_cart_item(product.id, user, db_session)
    await db_session.flush()
    with pytest.raises(IntegrityError):
        await insert_cart_item(product.id, user, db_session)
        await db_session.flush()


@pytest.mark.asyncio
async def test_update_cart_item(db_session):
    new_cart = cart_factory()
    new_cart_item = cart_item_factory(cart=new_cart)
    new_cart.total_items = 1
    db_session.add(new_cart_item)
    await db_session.flush()
    update_cart_item_data = update_cart_item_data_factory(
        new_cart_item.id, new_quantity=5
    )

    await update_cart_item_quantity_in_db(update_cart_item_data, db_session)

    cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert cart_item.quantity == update_cart_item_data.new_quantity
    assert new_cart.total_items == 5
