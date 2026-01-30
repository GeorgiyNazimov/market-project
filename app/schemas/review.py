from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NewReviewData(BaseModel):
    text: str
    product_rating: int


class ReviewData(BaseModel):
    created_at: datetime
    first_name: str | None
    last_name: str | None
    text: str
    product_rating: int

    model_config = ConfigDict(from_attributes=True)


class NextCursorData(BaseModel):
    created_at: datetime | None
    id: UUID | None


class ReviewDataList(BaseModel):
    reviews_list: List[ReviewData]
    next_cursor: NextCursorData
