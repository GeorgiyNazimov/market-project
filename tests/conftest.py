import asyncio

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import get_settings
from app.core.exception_handler import register_exception_handlers
from app.database.connection.session import (
    get_async_session_maker,
    get_engine,
)
from app.main import get_app
from app.services import user
from tests.factories.users import user_factory


@pytest.fixture(scope="session")
def test_settings():
    return get_settings(env_file=".env.test")


@pytest.fixture(scope="session")
async def test_engine(test_settings):
    engine = get_engine(test_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        test_settings.sync_database_uri,
    )
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")

    yield engine

    await engine.dispose()


@pytest.fixture(scope="session")
async def test_async_session_maker(test_engine):
    session_maker = get_async_session_maker(test_engine)
    yield session_maker


@pytest.fixture(scope="function")
async def db_session(test_engine):
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        async_session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        yield async_session
        await async_session.close()
        await transaction.rollback()


@pytest.fixture
def monkeypatch():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope="session")
def app():
    app = get_app()
    register_exception_handlers(app)
    return app


@pytest.fixture(scope="session")
async def async_client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def override_get_session(db_session):
    async def _override_get_session():
        yield db_session

    return _override_get_session


@pytest.fixture
def override_role_checker():
    async def _override_role_checker():
        return user_factory()

    return _override_role_checker


@pytest.fixture(scope="session", autouse=True)
def speed_up_passwords():
    fast_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
    user.pwd_context = fast_context


@pytest.fixture(autouse=True)
def clear_overrides(app):
    yield

    app.dependency_overrides.clear()
