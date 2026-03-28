from types import SimpleNamespace

from jose import jwt
import pytest
from sqlalchemy import select

from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.database.models.user import User
from app.services.user import get_user_data_serv, login_serv, create_user_serv
from tests.factories.users import new_user_data_factory, user_factory


@pytest.mark.asyncio
async def test_create_user_unique_email_success(db_session):
    new_user = new_user_data_factory()

    await create_user_serv(new_user, db_session)

    user_from_db = (await db_session.execute(select(User))).scalar_one()
    assert user_from_db.email == new_user.email
    assert user_from_db.password_hash == new_user.password


@pytest.mark.asyncio
async def test_create_user_same_email_error(db_session):
    new_user1 = new_user_data_factory(email="same_email@domain.com")
    new_user2 = new_user_data_factory(email="same_email@domain.com")

    await create_user_serv(new_user1, db_session)
    with pytest.raises(ConflictError):
        await create_user_serv(new_user2, db_session)


@pytest.mark.asyncio
async def test_login_user_success(db_session, test_settings):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    auth_data = SimpleNamespace(username=new_user.email, password="password")

    login_result = await login_serv(auth_data, db_session)

    token_data = jwt.decode(
        login_result.access_token,
        test_settings.SECRET_KEY,
        algorithms=[test_settings.ALGORITHM],
    )

    assert token_data["sub"] == str(new_user.id)
    assert token_data["role"] == new_user.role


@pytest.mark.asyncio
async def test_login_user_wrong_email_error(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    auth_data = SimpleNamespace(username="email", password="password")

    with pytest.raises(AuthenticationError):
        await login_serv(auth_data, db_session)


@pytest.mark.asyncio
async def test_login_user_wrong_password_error(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    auth_data = SimpleNamespace(username=new_user.email, password="test_password")

    with pytest.raises(AuthenticationError):
        await login_serv(auth_data, db_session)


@pytest.mark.asyncio
async def test_get_user_success(db_session):
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()

    user_data = await get_user_data_serv(new_user, db_session)

    assert user_data.email == new_user.email
    assert user_data.role == new_user.role


@pytest.mark.asyncio
async def test_get_user_not_found(db_session):
    new_user = user_factory()

    with pytest.raises(NotFoundError):
        await get_user_data_serv(new_user, db_session)
