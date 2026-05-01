from uuid import uuid4

import pytest

from app.core.exceptions import BadRequest, ConflictError, NotFoundError
from app.database.models.product import Product
from app.schemas.product import ProductUpdateData
from app.services.product import (
    create_product_serv,
    delete_product_serv,
    get_product_serv,
    update_product_serv,
)
from tests.factories.products import (
    new_product_data_factory,
    product_factory,
    product_update_data_factory,
)


@pytest.mark.asyncio
async def test_create_product_serv_success(db_session):
    new_product_data = new_product_data_factory(name=" product_name ")

    new_product_id = await create_product_serv(new_product_data, db_session)

    db_session.expunge_all()
    db_product = await db_session.get(Product, new_product_id)
    assert db_product.id == new_product_id
    assert db_product.name == new_product_data.name.strip()
    assert db_product.price == new_product_data.price
    assert db_product.stock == new_product_data.stock


@pytest.mark.asyncio
async def test_create_product_serv_duplicate_name_conflict_error(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()
    new_product_data = new_product_data_factory(name=product.name)

    with pytest.raises(ConflictError):
        await create_product_serv(new_product_data, db_session)


@pytest.mark.asyncio
async def test_get_product_data_serv_success(db_session):
    product = product_factory(product_rating_include=True)
    db_session.add(product)
    await db_session.flush()

    product_data = await get_product_serv(product.id, db_session)

    assert product_data.id == product.id
    assert product_data.name == product.name
    assert product_data.price == product.price
    assert product_data.stock == product.stock
    assert product_data.description == product.description
    assert product_data.product_rating.avg_rating == product.product_rating.avg_rating
    assert product_data.product_rating.rating_count == product.product_rating.rating_count
    for i in range(1, 6):
        field = f"rating_{i}_count"
        assert getattr(product_data.product_rating, field) == getattr(product.product_rating, field)


@pytest.mark.asyncio
async def test_get_product_data_serv_missing_id_not_found_error(db_session):
    with pytest.raises(NotFoundError):
        await get_product_serv(uuid4(), db_session)


@pytest.mark.asyncio
async def test_update_product_serv_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    product_update_data = product_update_data_factory()
    updated_id = await update_product_serv(
        product_id=product.id,
        product_update_data=product_update_data,
        session=db_session,
    )

    db_session.expunge_all()
    db_product = await db_session.get(Product, updated_id)
    assert updated_id == product.id
    assert db_product.name == product_update_data.name.strip()
    assert db_product.description == product_update_data.description
    assert db_product.price == product_update_data.price
    assert db_product.stock == product_update_data.stock


@pytest.mark.asyncio
async def test_update_product_serv_no_update_data_bad_request_error(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    product_update_data = ProductUpdateData()

    with pytest.raises(BadRequest):
        await update_product_serv(
            product_id=product.id,
            product_update_data=product_update_data,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_update_product_serv_duplicate_name_conflict_error(db_session):
    product1 = product_factory(name="name1")
    product2 = product_factory(name="name2")
    db_session.add_all([product1, product2])
    await db_session.flush()

    assert product1.name != product2.name

    product_update_data = product_update_data_factory(name="name1")

    with pytest.raises(ConflictError):
        await update_product_serv(
            product_id=product2.id,
            product_update_data=product_update_data,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_update_product_serv_missing_product_id_not_found_error(db_session):
    product_update_data = product_update_data_factory()

    with pytest.raises(NotFoundError):
        await update_product_serv(
            product_id=uuid4(),
            product_update_data=product_update_data,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_delete_product_serv_success(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    deleted_id = await delete_product_serv(product.id, db_session)

    db_session.expunge_all()
    db_product = await db_session.get(Product, product.id)
    assert db_product is None
    assert deleted_id == product.id


@pytest.mark.asyncio
async def test_delete_product_missing_id_not_found_error(db_session):
    product = product_factory()
    db_session.add(product)
    await db_session.flush()

    with pytest.raises(NotFoundError):
        await delete_product_serv(uuid4(), db_session)
