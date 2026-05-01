import pytest
from fastapi import status
from jose import jwt

from app.api.dependencies import get_session, get_token_data
from tests.factories.users import new_user_data_factory, user_factory


@pytest.mark.asyncio
async def test_login_user_success(
    db_session, async_client, app, override_get_session, test_settings
):
    password = "password"
    user = user_factory(password=password)
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    auth_data = {"username": user.email, "password": password}
    response = await async_client.post("/api/v1/users/token", data=auth_data)

    response = response.json()
    assert response["token_type"] == "bearer"

    token_data = jwt.decode(
        response["access_token"],
        test_settings.SECRET_KEY,
        algorithms=[test_settings.ALGORITHM],
    )

    assert token_data["sub"] == str(user.id)
    assert token_data["role"] == user.role


@pytest.mark.asyncio
async def test_login_user_wrong_password_error(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    auth_data = {"username": user.email, "password": "wrong_password"}
    response = await async_client.post("/api/v1/users/token", data=auth_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Invalid credential"


@pytest.mark.asyncio
async def test_login_user_wrong_email_error(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    auth_data = {"username": "wrong_email@mail.ru", "password": "password"}
    response = await async_client.post("/api/v1/users/token", data=auth_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Invalid credential"


@pytest.mark.asyncio
async def test_get_user_data_success(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_token_data] = lambda: user

    response = await async_client.get("/api/v1/users/me")
    user_data = response.json()

    assert user_data["email"] == user.email
    assert user_data["role"] == user.role


@pytest.mark.asyncio
async def test_get_user_data_unauthorized_error(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.get("/api/v1/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_register_user_success(async_client, app, override_get_session):
    user_create_data = new_user_data_factory()

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.post(
        "/api/v1/users/register", json=user_create_data.model_dump()
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "User registered successfully"


@pytest.mark.asyncio
async def test_register_user_not_unique_email_error(
    db_session, async_client, app, override_get_session
):
    user = user_factory()
    db_session.add(user)
    await db_session.flush()
    user_create_data = new_user_data_factory(email=user.email)

    app.dependency_overrides[get_session] = override_get_session

    response = await async_client.post(
        "/api/v1/users/register", json=user_create_data.model_dump()
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["error"]["message"] == "User already exists"
