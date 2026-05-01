from typing import AsyncGenerator

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import get_settings
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.database.connection.session import _async_session_maker
from app.schemas.user import UserTokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().PATH_PREFIX}/users/token"
)

settings = get_settings()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_maker() as session:
        yield session


async def get_token_data(token: str = Security(oauth2_scheme)) -> UserTokenData:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except ExpiredSignatureError as e:
        raise AuthenticationError("Expired token") from e
    except JWTError as e:
        raise AuthenticationError("Invalid credential") from e
    token_data = UserTokenData.model_validate(payload)
    return token_data


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, token: UserTokenData = Depends(get_token_data)):
        if token.role not in self.allowed_roles:
            raise ForbiddenError("Not enough permissions")
        return token
