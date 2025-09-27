from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models.user import User
from app.schemas.auth import UserCreateData

async def get_user_from_db(email: str, session: AsyncSession) -> User | None:
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    return user

async def create_user_in_db(userData: UserCreateData, session: AsyncSession) -> User:
    new_user = User(email=userData.email, password_hash=userData.password)
    session.add(new_user)
    try:
        await session.commit()
        await session.refresh(new_user)
    except:
        await session.rollback()
        raise 
    return new_user