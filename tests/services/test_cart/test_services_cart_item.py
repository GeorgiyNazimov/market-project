import pytest
from sqlalchemy import select

from app.core.exceptions import ConflictError, ForbiddenError
from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.services.cart import (
    create_cart_item_serv,
    delete_cart_item_serv,
    get_cart_items_serv,
    update_cart_item_quantity_serv,
)
from tests.factories.cart import (
    cart_factory,
    cart_item_factory,
    update_cart_item_data_factory,
)
from tests.factories.products import product_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_delete_cart_item_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_item = cart_item_factory(cart)
    db_session.add_all([user, cart, cart_item])
    await db_session.flush()

    await delete_cart_item_serv(cart_item.id, user, db_session)

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert db_cart_item is None


@pytest.mark.asyncio
async def test_delete_cart_item_other_user_forbidden_error(db_session):
    my_user = user_factory()
    other_cart_item = cart_item_factory()
    db_session.add_all([my_user, other_cart_item])
    await db_session.flush()

    with pytest.raises(ForbiddenError):
        await delete_cart_item_serv(other_cart_item.id, my_user, db_session)

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert db_cart_item == other_cart_item


@pytest.mark.asyncio
async def test_get_cart_item_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_items = [cart_item_factory(cart) for _ in range(3)]
    cart_item_ids = [item.id for item in cart_items]
    db_session.add_all([user, cart, *cart_items])
    await db_session.flush()

    db_cart_items = await get_cart_items_serv(None, user, db_session)

    for item in db_cart_items.cart_items:
        assert item.id in cart_item_ids


@pytest.mark.asyncio
async def test_get_cart_item_other_user_forbidden_error(db_session):
    my_user = user_factory()
    other_user = user_factory()
    other_cart = cart_factory(other_user)
    other_cart_items = [cart_item_factory(other_cart) for _ in range(3)]
    db_session.add_all([my_user, other_user, other_cart, *other_cart_items])
    await db_session.flush()

    with pytest.raises(ForbiddenError):
        await get_cart_items_serv(other_user.id, my_user, db_session)


@pytest.mark.asyncio
async def test_get_cart_item_admin_can_view_any(db_session):
    admin_user = user_factory(role="admin")
    other_user = user_factory()
    other_cart = cart_factory(other_user)
    other_cart_items = [cart_item_factory(other_cart) for _ in range(3)]
    cart_item_ids = [item.id for item in other_cart_items]
    db_session.add_all([admin_user, other_user, other_cart, *other_cart_items])
    await db_session.flush()

    db_cart_items = await get_cart_items_serv(other_user.id, admin_user, db_session)

    for item in db_cart_items.cart_items:
        assert item.id in cart_item_ids


@pytest.mark.asyncio
async def test_create_cart_item_success(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    new_cart_item = await create_cart_item_serv(product.id, user, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one()
    assert cart.user_id == user.id
    assert new_cart_item.product_id == product.id
    assert new_cart_item.cart_id == cart.id


@pytest.mark.asyncio
async def test_insert_cart_item_same_product_multiple_times_conflict_error(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    await create_cart_item_serv(product.id, user, db_session)
    with pytest.raises(ConflictError):
        await create_cart_item_serv(product.id, user, db_session)


@pytest.mark.asyncio
async def test_update_cart_item_quantity_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_item = cart_item_factory(cart)
    update_cart_item_data = update_cart_item_data_factory(cart_item.id, new_quantity=5)
    db_session.add_all([user, cart, cart_item])
    await db_session.flush()

    await update_cart_item_quantity_serv(update_cart_item_data, user, db_session)

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item.quantity == update_cart_item_data.new_quantity


@pytest.mark.asyncio
async def test_update_cart_item_quantity_other_user_forbidden_error(db_session):
    user = user_factory()
    cart_item = cart_item_factory()
    update_cart_item_data = update_cart_item_data_factory(cart_item.id, new_quantity=5)
    db_session.add_all([user, cart_item])
    await db_session.flush()

    with pytest.raises(ForbiddenError):
        await update_cart_item_quantity_serv(update_cart_item_data, user, db_session)

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item.quantity == cart_item.quantity
