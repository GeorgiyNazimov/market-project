import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from alembic import command
from alembic.config import Config
from app.config.default import get_settings
from app.database import Base
from app.database.connection.session import (
    get_async_session_maker,
    get_engine,
)
from app.main import get_app
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
async def db_session(test_async_session_maker, test_engine):
    async with test_async_session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))


@pytest.fixture
def monkeypatch():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture
def app():
    return get_app()


@pytest.fixture
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
def override_get_current_user():
    async def _override_get_current_user():
        return user_factory()

    return _override_get_current_user
