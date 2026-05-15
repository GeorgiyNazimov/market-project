import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.repositories.cart import (
    create_cart_item_repo,
    delete_cart_item_repo,
    delete_cart_items_by_ids_repo,
    get_cart_items_by_ids_repo,
    get_cart_items_by_user_id_repo,
    update_cart_item_quantity_repo,
)
from tests.factories.cart import (
    cart_factory,
    cart_item_factory,
    update_cart_item_data_factory,
)
from tests.factories.products import product_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_cart_item_success(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    new_cart_item = await create_cart_item_repo(product.id, user.id, db_session)

    cart = (await db_session.execute(select(Cart))).scalar_one()
    assert cart.user_id == user.id
    assert new_cart_item.product_id == product.id
    assert new_cart_item.cart_id == cart.id


@pytest.mark.asyncio
async def test_create_cart_item_same_product_multiple_times_integrity_error(db_session):
    product = product_factory()
    user = user_factory()
    db_session.add_all([product, user])
    await db_session.flush()

    await create_cart_item_repo(product.id, user.id, db_session)
    await db_session.flush()
    with pytest.raises(IntegrityError):
        await create_cart_item_repo(product.id, user.id, db_session)
        await db_session.flush()


@pytest.mark.asyncio
async def test_delete_cart_item_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_item = cart_item_factory(cart)
    db_session.add_all([user, cart, cart_item])
    await db_session.flush()

    deleted_cart_item = await delete_cart_item_repo(cart_item.id, user.id, db_session)
    assert deleted_cart_item.id == cart_item.id

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert db_cart_item is None


@pytest.mark.asyncio
async def test_delete_cart_item_other_user_returns_none(db_session):
    my_user = user_factory()
    other_cart_item = cart_item_factory()
    db_session.add_all([my_user, other_cart_item])
    await db_session.flush()

    deleted_cart_item = await delete_cart_item_repo(
        other_cart_item.id, my_user.id, db_session
    )
    assert deleted_cart_item is None

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item == other_cart_item


@pytest.mark.asyncio
async def test_delete_cart_items_by_ids_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_items = [cart_item_factory(cart) for _ in range(3)]
    db_session.add_all([user, cart, *cart_items])
    await db_session.flush()

    delete_ids = [cart_items[0].id, cart_items[1].id]
    deleted_item_ids = await delete_cart_items_by_ids_repo(
        delete_ids, user.id, db_session
    )

    for item_id in deleted_item_ids:
        assert item_id in delete_ids

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one()
    assert db_cart_item.id == cart_items[2].id


@pytest.mark.asyncio
async def test_delete_cart_items_by_ids_other_user_empty_result(db_session):
    user = user_factory()
    cart_items = [cart_item_factory() for _ in range(3)]
    db_session.add_all([user, *cart_items])
    await db_session.flush()

    delete_ids = [cart_items[0].id, cart_items[1].id]
    deleted_item_ids = await delete_cart_items_by_ids_repo(
        delete_ids, user.id, db_session
    )

    assert deleted_item_ids == []

    db_cart_items = (await db_session.execute(select(CartItem))).scalars().all()
    assert len(db_cart_items) == 3


@pytest.mark.asyncio
async def test_get_cart_items_by_user_id_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_items = [cart_item_factory(cart) for _ in range(3)]
    cart_item_ids = map(lambda x: x.id, cart_items)
    db_session.add_all([user, cart, *cart_items])
    await db_session.flush()

    db_cart_items, total_items = await get_cart_items_by_user_id_repo(
        user.id, db_session
    )

    for item in db_cart_items:
        assert item.id in cart_item_ids
    assert total_items == 3


@pytest.mark.asyncio
async def test_get_cart_items_by_user_id_empty_result(db_session):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    db_cart_items, total_items = await get_cart_items_by_user_id_repo(
        user.id, db_session
    )

    assert db_cart_items == []
    assert total_items == 0


@pytest.mark.asyncio
async def test_get_cart_items_by_ids_success(db_session):
    user = user_factory()
    products = [product_factory() for _ in range(3)]
    cart = cart_factory(user)
    cart_items = [cart_item_factory(cart, product) for product in products]
    cart_item_ids = [item.id for item in cart_items]
    db_session.add_all([user, cart, *cart_items])
    await db_session.flush()

    db_cart_items = await get_cart_items_by_ids_repo(cart_item_ids, user.id, db_session)

    for item in db_cart_items:
        assert item.id in cart_item_ids
        assert item.product in products
        assert item.cart.user.id == user.id


@pytest.mark.asyncio
async def test_get_cart_items_by_ids_other_user_empty_result(db_session):
    my_user = user_factory()
    other_cart_items = [cart_item_factory() for _ in range(3)]
    cart_item_ids = map(lambda x: x.id, other_cart_items)
    db_session.add_all([my_user, *other_cart_items])
    await db_session.flush()

    db_cart_items = await get_cart_items_by_ids_repo(
        cart_item_ids, my_user.id, db_session
    )

    assert db_cart_items == []


@pytest.mark.asyncio
async def test_update_cart_item_quantity_success(db_session):
    user = user_factory()
    cart = cart_factory(user)
    cart_item = cart_item_factory(cart)
    update_cart_item_data = update_cart_item_data_factory(
        cart_item.id,
        new_quantity=5,
    )
    db_session.add_all([user, cart, cart_item])
    await db_session.flush()

    updated_cart_item = await update_cart_item_quantity_repo(
        update_cart_item_data, user.id, db_session
    )

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert updated_cart_item.id == cart_item.id
    assert db_cart_item.quantity == update_cart_item_data.new_quantity


@pytest.mark.asyncio
async def test_update_cart_item_quantity_other_user_empty_result(db_session):
    my_user = user_factory()
    other_cart_item = cart_item_factory()
    update_cart_item_data = update_cart_item_data_factory(
        other_cart_item.id,
        new_quantity=5,
    )
    db_session.add_all([my_user, other_cart_item])
    await db_session.flush()

    updated_cart_item = await update_cart_item_quantity_repo(
        update_cart_item_data, my_user.id, db_session
    )

    db_cart_item = (await db_session.execute(select(CartItem))).scalar_one_or_none()
    assert updated_cart_item is None
    assert db_cart_item.quantity == other_cart_item.quantity
