from datetime import timedelta
from types import SimpleNamespace
from fastapi import HTTPException
from sqlalchemy import select
from app.database.models.user import User
from app.services.auth import create_access_token, get_current_user
import pytest

from tests.factories.users import new_user_data_factory, user_factory

@pytest.mark.asyncio
async def test_get_current_user(db_session, monkeypatch, test_settings):
    monkeypatch.setattr("app.services.auth.settings", test_settings)
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    token = create_access_token(
        {"sub": new_user.email},
        expires_delta=timedelta(minutes=30),
    )

    user = await get_current_user(token, db_session)
    
    assert user.email == new_user.email
    assert user.password_hash == new_user.password_hash

@pytest.mark.asyncio
async def test_get_current_user_wrong_token(db_session, monkeypatch, test_settings):
    monkeypatch.setattr("app.services.auth.settings", test_settings)
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    token = "token"

    with pytest.raises(HTTPException):
        await get_current_user(token, db_session)

@pytest.mark.asyncio
async def test_get_current_user_expired_token(db_session, monkeypatch, test_settings):
    monkeypatch.setattr("app.services.auth.settings", test_settings)
    new_user = user_factory()
    db_session.add(new_user)
    await db_session.flush()
    token = create_access_token(
        {"sub": new_user.email},
        expires_delta=timedelta(minutes=-1),
    )

    with pytest.raises(HTTPException):
        await get_current_user(token, db_session)

@pytest.mark.asyncio
async def test_get_current_user_user_not_found(db_session, monkeypatch, test_settings):
    monkeypatch.setattr("app.services.auth.settings", test_settings)
    token = create_access_token(
        {"sub": "email"},
        expires_delta=timedelta(minutes=30),
    )

    with pytest.raises(HTTPException):
        await get_current_user(token, db_session)
