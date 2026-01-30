from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings, Settings


def get_engine(settings: Settings):
    return create_async_engine(
        settings.database_uri,
        echo=False,
        future=True,
        pool_size=20,
        max_overflow=5,
    )

def get_async_session_maker(engine) -> sessionmaker:
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_engine = None
_async_session_maker = None

def init_db(settings=None):
    global _engine, _async_session_maker

    if _engine is not None:
        return

    if settings is None:
        settings = get_settings()

    print("ENGINE INIT WITH:", settings.POSTGRES_HOST)

    _engine = get_engine(settings)
    _async_session_maker = get_async_session_maker(_engine)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _async_session_maker is None:
        print("Initializing DB without settings!")
        init_db()
    
    async with _async_session_maker() as session:
        yield session
