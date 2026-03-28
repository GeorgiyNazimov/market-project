from decimal import Decimal

import pytest
from sqlalchemy import select

from app.database.models.order import Order
from app.database.models.order_item import OrderItem
from app.repositories.orders import (
    add_order_items_repo,
    create_order_repo,
    delete_order_repo,
    get_order_by_id_repo,
    get_orders_by_user_id_repo,
    update_order_total_price_repo,
)
from tests.factories.orders import order_factory, order_item_factory
from tests.factories.products import product_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_order(db_session):
    user = user_factory()
    db_session.add(user)

    order = await create_order_repo(user.id, db_session)

    db_session.expunge_all()

    db_order = await db_session.get(Order, order.id)

    assert db_order.id == order.id
    assert db_order.user_id == user.id
    assert db_order.status == "pending"


@pytest.mark.asyncio
async def test_add_order_items(db_session):
    user = user_factory()
    order = order_factory(user=user)
    order_items = [order_item_factory(order=order) for _ in range(3)]
    db_session.add_all([user, order])

    await add_order_items_repo(order_items, db_session)

    db_session.expunge_all()

    db_order_items = (await db_session.execute(select(OrderItem))).scalars().all()

    assert len(db_order_items) == 3
    assert db_order_items[0].order_id == order.id


@pytest.mark.asyncio
async def test_get_orders_by_user_id(db_session):
    user1 = user_factory()
    user2 = user_factory()
    order1 = order_factory(user=user1)
    order2 = order_factory(user=user1)
    order3 = order_factory(user=user2)
    db_session.add_all([user1, user2, order1, order2, order3])

    db_orders = await get_orders_by_user_id_repo(user1.id, db_session)

    assert len(db_orders) == 2
    for ord in db_orders:
        assert ord.user_id == user1.id


@pytest.mark.asyncio
async def test_get_order_by_id(db_session):
    user1 = user_factory()
    user2 = user_factory()
    order1 = order_factory(user=user1)
    db_session.add_all([user1, user2, order1])

    res = await get_order_by_id_repo(order1.id, user2.id, db_session)
    assert res is None

    empty_filter_res = await get_order_by_id_repo(order1.id, None, db_session)
    assert empty_filter_res is not None
    assert empty_filter_res.user_id == user1.id


@pytest.mark.asyncio
async def test_get_order_eager_loading(db_session):
    user = user_factory()
    product = product_factory()
    order = order_factory(user=user)
    order_item = order_item_factory(order=order, product=product)
    db_session.add_all([user, product, order, order_item])
    await db_session.flush()

    db_session.expunge_all()

    db_order = await get_order_by_id_repo(order.id, None, db_session)

    assert db_order is not None
    assert len(db_order.items) == 1
    assert db_order.items[0].product.name == product.name


@pytest.mark.asyncio
async def test_update_order_total_price(db_session):
    user = user_factory()
    order = order_factory(user=user)
    db_session.add_all([user, order])
    new_price = Decimal("123.45")

    res_id = await update_order_total_price_repo(order.id, new_price, db_session)
    assert res_id == order.id

    db_session.expunge_all()

    order_updated_data = (await db_session.execute(select(Order))).scalar_one()

    assert order_updated_data.id == order.id
    assert order_updated_data.total_price == new_price


@pytest.mark.asyncio
async def test_delete_order_repo_security(db_session):
    user1 = user_factory()
    user2 = user_factory()
    order1 = order_factory(user1)
    db_session.add_all([user1, user2, order1])

    deleted_id = await delete_order_repo(order1.id, user2.id, db_session)
    assert deleted_id is None

    db_session.expunge_all()

    exists = await db_session.get(Order, order1.id)
    assert exists is not None


@pytest.mark.asyncio
async def test_delete_order_success(db_session):
    user = user_factory()
    order = order_factory(user)
    db_session.add_all([user, order])

    deleted_id = await delete_order_repo(order.id, user.id, db_session)
    assert deleted_id == order.id

    db_session.expunge_all()

    exists = await db_session.get(Order, order.id)
    assert exists is None
