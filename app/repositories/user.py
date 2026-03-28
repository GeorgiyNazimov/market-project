from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.schemas.user import UserCreateData


async def get_user_by_email_repo(email: str, session: AsyncSession) -> User | None:
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    return user


async def get_user_by_id_repo(user_id: str, session: AsyncSession) -> User | None:
    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    return user


async def create_user_repo(user_data: UserCreateData, session: AsyncSession) -> User:
    new_user = User(email=user_data.email, password_hash=user_data.password)
    session.add(new_user)
    return new_user
