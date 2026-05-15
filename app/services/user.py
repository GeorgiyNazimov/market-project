import logging
from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.database.models.user import User
from app.repositories.user import (
    create_user_repo,
    get_user_by_email_repo,
    get_user_by_id_repo,
)
from app.schemas.user import Token, UserCreateData, UserGetData, UserTokenData

logger = logging.getLogger("service.auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def login_serv(
    auth_data: OAuth2PasswordRequestForm, session: AsyncSession
) -> Token:
    user = await get_user_by_email_repo(auth_data.username, session)

    if not user:
        raise AuthenticationError("Invalid credential")
    if not verify_password(auth_data.password, user.password_hash):
        raise AuthenticationError("Invalid credential")

    logger.info("login_success", extra={"user_id": user.id})
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def create_user_serv(user_data: UserCreateData, session: AsyncSession) -> User:
    try:
        user_data.password = get_password_hash(user_data.password)
        new_user = await create_user_repo(user_data, session)
        await session.commit()
        logger.info(
            "user_create_success",
            extra={
                "user_id": new_user.id,
                "role": new_user.role,
            },
        )
    except IntegrityError as e:
        await session.rollback()
        raise ConflictError("User already exists") from e
    return new_user


async def get_user_data_serv(
    token_data: UserTokenData, session: AsyncSession
) -> UserGetData:
    user = await get_user_by_id_repo(token_data.id, session)
    if not user:
        logger.error("user_not_found_with_valid_token")
        raise NotFoundError("User not found")
    return UserGetData.model_validate(user)
