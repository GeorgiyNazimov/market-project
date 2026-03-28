from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

SafeRole = Annotated[str, BeforeValidator(lambda role: role or "user")]


class UserCreateData(BaseModel):
    email: str
    password: str


class UserGetData(BaseModel):
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    created_at: datetime
    role: SafeRole

    model_config = ConfigDict(from_attributes=True)


class CurrentUserData(BaseModel):
    id: UUID = Field(alias="sub")
    role: SafeRole
    exp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class Token(BaseModel):
    access_token: str
    token_type: str
