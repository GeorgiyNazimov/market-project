import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import status

from app.database.connection.session import get_session
from app.database.models.review import Review
from app.repositories.review import create_product_review_db
from app.services.auth import get_current_user
from tests.factories.products import product_factory
from tests.factories.reviews import new_review_data_factory
from tests.factories.users import user_factory

@pytest.mark.asyncio
async def test_create_review(db_session, async_client, app, override_get_session):
    new_product = product_factory()
    new_user = user_factory()
    new_review_data = new_review_data_factory()
    db_session.add_all([new_user, new_product])
    await db_session.flush()

    def override_get_current_user():
        yield new_user

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    response = await async_client.post(f"/api/v1/reviews/{new_product.id}/create_review", json=new_review_data.model_dump())
    assert response.status_code == status.HTTP_200_OK

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.product_id == new_product.id
    assert review.user_id == new_user.id
    assert review.text == new_review_data.text
