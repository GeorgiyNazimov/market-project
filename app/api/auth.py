from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import Settings, get_settings
from app.database.connection.session import get_session
from app.database.models.user import User
from app.schemas.auth import UserCreateData, UserGetData
from app.services.auth import create_user, authenticate_user, create_access_token, get_current_user

app = APIRouter(prefix="/auth", tags=["Authentication"])


@app.post("/token")
async def login(
    authData: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session)
    ):
    user = await authenticate_user(authData, session)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)) -> UserGetData:
    return UserGetData.model_validate(current_user)

@app.post("/register")
async def register_user(userData: UserCreateData, session: AsyncSession = Depends(get_session)):
    await create_user(userData, session)
    return {"msg": "User registered successfully"}
