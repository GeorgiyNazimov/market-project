from uuid import UUID

from fastapi import Query
from pydantic import BaseModel


class IdResponse(BaseModel):
    id: UUID


class StatusResponse(BaseModel):
    status: str = "ok"
    message: str | None = None


class PaginationParams(BaseModel):
    sort_by: str = "created_at"
    cursor: str | None = None
    limit: int = Query(10, ge=1, le=100)
