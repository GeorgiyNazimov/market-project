import asyncio

from sqlalchemy import select, update

from app.api.dependencies import get_session
from app.database.models.user import User

BATCH_SIZE = 1000


async def set_default_roles_for_users():
    async for session in get_session():
        while True:
            subq = (
                select(User.id)
                .where(User.role == None)
                .limit(1000)
                .with_for_update(skip_locked=True)
            ).scalar_subquery()

            stmt = (
                update(User)
                .where(User.id.in_(subq))
                .values(role = "user")
                .returning(User.id)
            )

            results = (await session.execute(stmt)).scalars().all()

            if not results:
                break

            await session.commit()
            print(f"Processed {len(results)} rows...")


if __name__ == "__main__":
    asyncio.run(set_default_roles_for_users())
