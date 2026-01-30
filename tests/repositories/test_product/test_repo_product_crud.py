from sqlalchemy import select
from app.database.models.product import Product
from app.repositories.products import create_product, get_product_data_from_db
from tests.factories.products import new_product_data_factory, product_factory
import pytest

@pytest.mark.asyncio
async def test_create_product(db_session):
    new_product_data = new_product_data_factory()

    await create_product(new_product_data, db_session)

    product = (await db_session.execute(select(Product))).scalar_one()
    assert product.name == new_product_data.name
    assert product.price == new_product_data.price
    assert product.stock == new_product_data.stock

@pytest.mark.asyncio
async def test_get_product_data(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    await db_session.flush()

    product_data = await get_product_data_from_db(new_product.id, db_session)

    assert product_data.id == new_product.id
    assert product_data.name == new_product.name
    assert product_data.price == new_product.price