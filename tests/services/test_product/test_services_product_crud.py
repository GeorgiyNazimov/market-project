import pytest
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.database.models.product import Product
from app.database.models.review import Review
from app.services.products import add_product_in_market, create_product_review_serv, get_product_data_serv
from tests.factories.products import new_product_data_factory, product_factory
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import user_factory


@pytest.mark.asyncio
async def test_create_product(db_session):
    new_product_data = new_product_data_factory()

    await add_product_in_market(new_product_data, db_session)

    product = (await db_session.execute(select(Product))).scalar_one()
    assert product.name == new_product_data.name
    assert product.price == new_product_data.price
    assert product.stock == new_product_data.stock


@pytest.mark.asyncio
async def test_get_product_data(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    await db_session.flush()

    product_data = await get_product_data_serv(new_product.id, db_session)

    assert product_data.id == new_product.id
    assert product_data.name == new_product.name
    assert product_data.price == new_product.price


@pytest.mark.asyncio
async def test_create_review(db_session):
    new_product = product_factory()
    new_user = user_factory()
    new_review_data = new_review_data_factory()
    db_session.add_all([new_user, new_product])
    await db_session.flush()

    await create_product_review_serv(new_product.id, new_review_data, new_user, db_session)

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == new_product.id
    assert review.user_id == new_user.id
    assert review.text == new_review_data.text


@pytest.mark.asyncio
async def test_cannot_create_review_for_unknown_product(db_session):
    new_product = product_factory()
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    new_review_data = new_review_data_factory()

    with pytest.raises(NotFoundError):
        await create_product_review_serv(
            new_product.id, new_review_data, new_user, db_session
        )


@pytest.mark.asyncio
async def test_cannot_create_review_by_unknown_user(db_session):
    new_product = product_factory()
    db_session.add(new_product)
    new_user = user_factory()
    await db_session.flush()
    new_review_data = new_review_data_factory()

    with pytest.raises(NotFoundError):
        await create_product_review_serv(
            new_product.id, new_review_data, new_user, db_session
        )
