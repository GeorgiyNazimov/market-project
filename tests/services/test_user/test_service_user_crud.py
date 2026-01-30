from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.database.models.user import User
from app.services.auth import authenticate_user, create_user
from tests.factories.users import new_user_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_user_unique_email(db_session):
    new_user = new_user_data_factory()

    await create_user(new_user, db_session)

    user_from_db = (await db_session.execute(select(User))).scalar_one()
    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password


@pytest.mark.asyncio
async def test_create_user_same_email(db_session):
    new_user1 = new_user_data_factory(email="same_email@domain.com")
    new_user2 = new_user_data_factory(email="same_email@domain.com")

    await create_user(new_user1, db_session)
    with pytest.raises(HTTPException):
        await create_user(new_user2, db_session)


@pytest.mark.asyncio
async def test_authenticate_user(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    auth_data = SimpleNamespace(username=new_user.email, password="password")

    user_from_db = await authenticate_user(auth_data, db_session)

    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password_hash


@pytest.mark.asyncio
async def test_authenticate_user_wrong_email(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    auth_data = SimpleNamespace(username="email", password="password")

    user_from_db = await authenticate_user(auth_data, db_session)

    assert user_from_db is False


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    auth_data = SimpleNamespace(username=new_user.email, password="test_password")

    user_from_db = await authenticate_user(auth_data, db_session)

    assert user_from_db is False
