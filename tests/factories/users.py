from datetime import datetime
from uuid import uuid4

from app.database.models.user import User
from app.schemas.auth import UserCreateData
from app.services.auth import get_password_hash


def user_factory(
    email: str | None = None,
    password="password",
    **kwargs,
) -> User:
    email = email or f"{uuid4()}@domain.com"
    return User(
        id=kwargs.get("id", uuid4()),
        email=email,
        first_name=kwargs.get("first_name", "first_name"),
        last_name=kwargs.get("last_name", "last_name"),
        role=kwargs.get("role", "user"),
        password_hash=get_password_hash(password),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )


def new_user_data_factory(
    email=f"{uuid4()}@domain.com",
    password="password",
) -> UserCreateData:
    return UserCreateData(email=email, password=password)
