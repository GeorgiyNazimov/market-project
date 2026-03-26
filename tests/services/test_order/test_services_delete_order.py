import pytest
from app.services.orders import delete_order_serv
from app.core.exceptions import NotFoundError, ForbiddenError
from app.database.models import Order, Product
from tests.factories.users import user_factory
from tests.factories.orders import order_factory, order_item_factory
from tests.factories.products import product_factory

@pytest.mark.asyncio
async def test_delete_order_success_restores_stock(db_session):
    user = user_factory()
    product = product_factory(stock=10)
    order = order_factory(user=user)
    order_item = order_item_factory(order=order, product=product, quantity=3)
    db_session.add_all([user, product, order, order_item])
    await db_session.flush()

    await delete_order_serv(order.id, user, db_session)

    db_session.expunge_all()
    
    db_order = await db_session.get(Order, order.id)
    assert db_order is None
    
    db_product = await db_session.get(Product, product.id)
    assert db_product.stock == 13

@pytest.mark.asyncio
async def test_delete_order_admin_success(db_session):
    admin = user_factory(role="admin")
    user = user_factory()
    order = order_factory(user=user)
    order_item = order_item_factory(order=order)
    db_session.add_all([admin, user, order, order_item])
    await db_session.flush()

    await delete_order_serv(order.id, admin, db_session)
    
    db_session.expunge_all()

    db_order = await db_session.get(Order, order.id)
    assert db_order is None

@pytest.mark.asyncio
async def test_delete_order_forbidden_for_other_user(db_session):
    my_user = user_factory()
    other_user = user_factory()
    other_order = order_factory(user=other_user)
    db_session.add_all([my_user, other_user, other_order])
    await db_session.flush()

    with pytest.raises(NotFoundError):
        await delete_order_serv(other_order.id, my_user, db_session)

    db_session.expunge_all()

    db_order = await db_session.get(Order, other_order.id)
    assert db_order is not None
