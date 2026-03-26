import pytest
from app.services.orders import get_orders_by_user_id_serv
from app.core.exceptions import ForbiddenError
from tests.factories.products import product_factory
from tests.factories.users import user_factory
from tests.factories.orders import order_factory, order_item_factory

@pytest.mark.asyncio
async def test_get_user_orders_own_success(db_session):
    user = user_factory()
    product = product_factory(name="Test Item")
    orders = [order_factory(user=user) for _ in range(3)]
    
    db_session.add_all(orders + [user, product])
    await db_session.flush()

    for o in orders:
        db_session.add(order_item_factory(order=o, product=product))
    await db_session.flush()

    res = await get_orders_by_user_id_serv(None, user, db_session)

    assert len(res.orders) == 3
    for order_read in res.orders:
        assert len(order_read.items) == 1
        assert order_read.items[0].product_name == "Test Item"

@pytest.mark.asyncio
async def test_get_orders_admin_can_view_any(db_session):
    admin = user_factory(role="admin")
    other_user = user_factory()
    product = product_factory(name="Admin View Product")
    order = order_factory(user=other_user)
    order_item = order_item_factory(order=order, product=product)
    
    db_session.add_all([admin, other_user, order, order_item, product])
    await db_session.flush()

    res = await get_orders_by_user_id_serv(other_user.id, admin, db_session)

    assert len(res.orders) == 1
    assert res.orders[0].id == order.id
    assert res.orders[0].items[0].product_name == "Admin View Product"

@pytest.mark.asyncio
async def test_get_orders_forbidden_for_other_user(db_session):
    user_me = user_factory()
    user_other = user_factory()
    db_session.add_all([user_me, user_other, order_factory(user=user_other)])
    await db_session.flush()

    with pytest.raises(ForbiddenError) as exc:
        await get_orders_by_user_id_serv(user_other.id, user_me, db_session)
    
    assert "You can only view your own orders" in str(exc.value)
