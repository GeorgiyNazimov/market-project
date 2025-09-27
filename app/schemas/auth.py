from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class UserCreateData(BaseModel):
    email: str
    password: str

class UserGetData(BaseModel):
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)