import pytest
from decimal import Decimal
from sqlalchemy import select
from app.database.models import Order, OrderItem, Product, CartItem
from app.core.exceptions import BadRequest, ForbiddenError
from app.schemas.orders import OrderCreate
from app.services.orders import create_order_serv
from tests.factories.cart import cart_factory, cart_item_factory
from tests.factories.products import product_factory
from tests.factories.users import user_factory

@pytest.mark.asyncio
async def test_create_order_serv_success(db_session):
    user = user_factory()
    cart = cart_factory(user=user)
    product = product_factory(stock=10, price=Decimal("150.00"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=3)
    db_session.add_all([user, product, cart_item])
    await db_session.flush()

    data = OrderCreate(cart_item_ids=[cart_item.id])

    order_read = await create_order_serv(data, user, db_session)

    assert order_read.total_price == Decimal("450.00")
    assert len(order_read.items) == 1
    
    db_session.expunge_all()
    
    product_in_db = await db_session.get(Product, product.id)
    assert product_in_db.stock == 7
    
    cart_item_in_db = await db_session.get(CartItem, cart_item.id)
    assert cart_item_in_db is None

@pytest.mark.asyncio
async def test_create_order_serv_insufficient_stock_rollback(db_session):
    user = user_factory()
    cart = cart_factory(user=user)
    product = product_factory(stock=1, price=Decimal("100"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=5)
    db_session.add_all([user, product, cart_item])
    await db_session.flush()

    data = OrderCreate(cart_item_ids=[cart_item.id])

    with pytest.raises(BadRequest) as exc:
        await create_order_serv(data, user, db_session)
    
    assert "Insufficient stock" in exc.value.message

    db_session.expunge_all()

    db_order = await db_session.execute(select(Order).where(Order.user_id == user.id))
    assert db_order.scalar_one_or_none() is None

    db_product = await db_session.get(Product, product.id)
    assert db_product.stock == 1

    db_cart_item = await db_session.get(CartItem, cart_item.id)
    assert db_cart_item is not None

@pytest.mark.asyncio
async def test_create_order_foreign_ids_rollback(db_session):
    my_user = user_factory()
    my_cart = cart_factory(user=my_user)
    other_user = user_factory()
    other_cart = cart_factory(user=other_user)
    product = product_factory(stock=10)
    
    my_cart_item = cart_item_factory(cart=my_cart, product=product)
    other_cart_item = cart_item_factory(cart=other_cart, product=product)
    
    db_session.add_all([my_user, other_user, product, my_cart_item, other_cart_item])
    await db_session.flush()

    data = OrderCreate(cart_item_ids=[my_cart_item.id, other_cart_item.id])

    with pytest.raises(ForbiddenError) as exc:
        await create_order_serv(data, my_user, db_session)
    
    assert "You can only select items from your cart" in str(exc.value)

    db_session.expunge_all()

    db_order = await db_session.execute(select(Order).where(Order.user_id == my_user.id))
    assert db_order.scalar_one_or_none() is None

    db_product = await db_session.get(Product, product.id)
    assert db_product.stock == 10

    db_cart_item = await db_session.get(CartItem, my_cart_item.id)
    assert db_cart_item is not None

@pytest.mark.asyncio
async def test_create_order_empty_list_forbidden(db_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    data = OrderCreate(cart_item_ids=[])

    with pytest.raises(ForbiddenError):
        await create_order_serv(data, user, db_session)
    
    db_order = await db_session.execute(select(Order).where(Order.user_id == user.id))
    assert db_order.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_create_order_uses_actual_price(db_session):
    user = user_factory()
    cart = cart_factory(user=user)
    product = product_factory(stock=10, price=Decimal("100.00"))
    cart_item = cart_item_factory(cart=cart, product=product, quantity=1)
    db_session.add_all([user, product, cart_item])
    await db_session.flush()

    product.price = Decimal("250.00")
    await db_session.flush()

    data = OrderCreate(cart_item_ids=[cart_item.id])

    order_read = await create_order_serv(data, user, db_session)

    assert order_read.total_price == Decimal("250.00")
    
    db_session.expunge_all()

    res = await db_session.execute(
        select(OrderItem).where(OrderItem.order_id == order_read.id)
    )
    db_order_item = res.scalar_one()
    assert db_order_item.price == Decimal("250.00")
