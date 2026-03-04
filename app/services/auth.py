from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.database.models.user import User
from app.repositories.auth import create_user_in_db, get_user_from_db
from app.schemas.auth import UserCreateData

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



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


async def create_user(userData: UserCreateData, session: AsyncSession) -> User:
    try:
        userData.password = get_password_hash(userData.password)
        new_user = await create_user_in_db(userData, session)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise ConflictError("User already exists") from e
    return new_user
