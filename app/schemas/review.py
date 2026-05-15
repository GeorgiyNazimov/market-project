from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NewReviewData(BaseModel):
    text: str
    product_rating: int


class ReviewUserData(BaseModel):
    first_name: str | None
    last_name: str | None

    model_config = ConfigDict(from_attributes=True)


class ReviewData(BaseModel):
    id: UUID
    created_at: datetime
    user: ReviewUserData
    text: str
    product_rating: int

    model_config = ConfigDict(from_attributes=True)


class ReviewDataList(BaseModel):
    review_list: List[ReviewData]
    next_cursor: str | None


class ReviewUpdateData(BaseModel):
    text: str | None = None
    product_rating: int | None = None

    model_config = ConfigDict(from_attributes=True)
