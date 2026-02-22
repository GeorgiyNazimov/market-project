from datetime import datetime, timedelta

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.database.connection.session import get_session
from app.database.models.user import User
from app.repositories.auth import create_user_in_db, get_user_from_db
from app.schemas.auth import UserCreateData

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Точка входа для Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().PATH_PREFIX}/auth/token"
)


settings = get_settings()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(
    authData: OAuth2PasswordRequestForm, session: AsyncSession
) -> User:
    user = await get_user_from_db(authData.username, session)
    if not user:
        raise AuthenticationError("Invalid credential")
    if not verify_password(authData.password, user.password_hash):
        raise AuthenticationError("Invalid credential")
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


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


async def create_user(userData: UserCreateData, session: AsyncSession) -> User:
    try:
        userData.password = get_password_hash(userData.password)
        new_user = await create_user_in_db(userData, session)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise ConflictError("User already exists") from e
    return new_user
