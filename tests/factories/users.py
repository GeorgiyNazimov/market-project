from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.database.models.user import User
from app.schemas.user import UserCreateData, UserTokenData
from app.services.user import get_password_hash


def user_factory(
    email: str | None = None,
    password: str = "password",
    **kwargs,
) -> User:
    email = email or f"{uuid4()}@domain.com"
    return User(
        id=kwargs.get("id", uuid4()),
        email=email if email is not None else f"{uuid4()}@domain.com",
        first_name=kwargs.get("first_name", "first_name"),
        last_name=kwargs.get("last_name", "last_name"),
        role=kwargs.get("role", "user"),
        password_hash=get_password_hash(password),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
    )


def new_user_data_factory(
    email: str | None = None,
    password: str = "password",
) -> UserCreateData:
    return UserCreateData(
        email=email if email is not None else f"{uuid4()}@domain.com",
        password=password,
    )


def token_data_factory(
    user: User | None = None,
    exp: datetime | None = None,
):
    user = user or user_factory()
    return UserTokenData(
        sub=user.id,
        role=user.role,
        exp=exp if exp is not None else datetime.now(timezone.utc) + timedelta(minutes=30),
    )
