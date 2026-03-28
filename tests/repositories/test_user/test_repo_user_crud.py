from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.models.user import User
from app.repositories.user import (
    create_user_repo,
    get_user_by_email_repo,
    get_user_by_id_repo,
)
from app.services.user import get_password_hash
from tests.factories.users import new_user_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_user_unique_email_success(db_session):
    new_user = new_user_data_factory()
    new_user.password = get_password_hash(new_user.password)

    await create_user_repo(new_user, db_session)

    user_from_db = (await db_session.execute(select(User))).scalar_one()
    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password


@pytest.mark.asyncio
async def test_create_user_same_email_error(db_session):
    new_user1 = new_user_data_factory(email="same_email@domain.com")
    new_user1.password = get_password_hash(new_user1.password)
    new_user2 = new_user_data_factory(email="same_email@domain.com")
    new_user2.password = get_password_hash(new_user2.password)

    await create_user_repo(new_user1, db_session)
    await db_session.flush()
    with pytest.raises(IntegrityError):
        await create_user_repo(new_user2, db_session)
        await db_session.flush()


@pytest.mark.asyncio
async def test_get_user_by_email_success(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()

    user_from_db = await get_user_by_email_repo(new_user.email, db_session)

    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password_hash


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session):
    user_from_db = await get_user_by_email_repo("random@mail.ru", db_session)

    assert user_from_db is None


@pytest.mark.asyncio
async def test_get_user_by_id_success(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()

    user_from_db = await get_user_by_id_repo(new_user.id, db_session)

    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password_hash


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session):
    user_from_db = await get_user_by_id_repo(uuid4(), db_session)

    assert user_from_db is None
