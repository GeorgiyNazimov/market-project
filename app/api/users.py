from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_token_data
from app.schemas.user import CurrentUserData, Token, UserCreateData, UserGetData
from app.services.user import (
    login_serv,
    create_user_serv,
    get_user_data_serv,
)

app = APIRouter(prefix="/users", tags=["Users"])


@app.post("/token")
async def login_handler(
    auth_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Token:
    token = await login_serv(auth_data, session)
    return token


@app.get("/me")
async def get_user_data_handler(
    current_user: CurrentUserData = Depends(get_token_data),
    session: AsyncSession = Depends(get_session),
) -> UserGetData:
    user_data = await get_user_data_serv(current_user, session)
    return user_data


@app.post("/register")
async def register_user_handler(
    user_data: UserCreateData, session: AsyncSession = Depends(get_session)
):
    await create_user_serv(user_data, session)
    return "User registered successfully"
