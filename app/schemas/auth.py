from datetime import datetime
from uuid import UUID
from typing import Annotated

from pydantic import BaseModel, ConfigDict, BeforeValidator, Field

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
