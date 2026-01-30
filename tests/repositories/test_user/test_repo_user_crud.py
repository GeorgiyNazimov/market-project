import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.user import User
from app.repositories.auth import create_user_in_db, get_user_from_db
from app.services.auth import get_password_hash
from tests.factories.users import new_user_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_user_unique_email(db_session):
    new_user = new_user_data_factory()
    new_user.password = get_password_hash(new_user.password)

    await create_user_in_db(new_user, db_session)

    user_from_db = (await db_session.execute(select(User))).scalar_one()
    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password


@pytest.mark.asyncio
async def test_create_user_same_email(db_session):
    new_user1 = new_user_data_factory(email="same_email@domain.com")
    new_user1.password = get_password_hash(new_user1.password)
    new_user2 = new_user_data_factory(email="same_email@domain.com")
    new_user2.password = get_password_hash(new_user2.password)

    await create_user_in_db(new_user1, db_session)
    with pytest.raises(IntegrityError):
        await create_user_in_db(new_user2, db_session)


@pytest.mark.asyncio
async def test_get_user(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()

    user_from_db = await get_user_from_db(new_user.email, db_session)

    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password_hash
