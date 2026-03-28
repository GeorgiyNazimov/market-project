from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_session, settings
from app.schemas.auth import CurrentUserData, UserCreateData, UserGetData
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_user_data,
)

app = APIRouter(prefix="/auth", tags=["Authentication"])


@app.post("/token")
async def login(
    authData: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(authData, session)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(
    current_user: CurrentUserData = Depends(RoleChecker(["user", "admin"])),
    session: AsyncSession = Depends(get_session),
) -> UserGetData:
    user_data = await get_user_data(current_user, session)
    return user_data


@app.post("/register")
async def register_user(
    userData: UserCreateData, session: AsyncSession = Depends(get_session)
):
    await create_user(userData, session)
    return {"msg": "User registered successfully"}
