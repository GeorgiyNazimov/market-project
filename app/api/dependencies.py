from typing import AsyncGenerator

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import get_settings
from app.core.exceptions import AuthenticationError
from app.database.connection.session import _async_session_maker
from app.database.models.user import User
from app.repositories.auth import get_user_from_db


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().PATH_PREFIX}/auth/token"
)

settings = get_settings()

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_maker() as session:
        yield session

async def get_current_user(
    token: str = Security(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
    except ExpiredSignatureError as e:
        raise AuthenticationError("Expired token") from e
    except JWTError as e:
        raise AuthenticationError("Invalid credential") from e
    user = await get_user_from_db(email, session) if email else None
    if user is None:
        raise AuthenticationError("Invalid credential")
    return user