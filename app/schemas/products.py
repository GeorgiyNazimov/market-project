from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ShortProductData(BaseModel):
    id: UUID
    name: str
    price: float
    stock: int
    category_id: UUID | None
    created_at: datetime
    avg_rating: float
    rating_count: int

    model_config = ConfigDict(from_attributes=True)


class NextCursorData(BaseModel):
    created_at: datetime
    id: UUID


class ShortProductDataList(BaseModel):
    product_list: List[ShortProductData]
    next_cursor: NextCursorData


class ProductData(BaseModel):
    id: UUID
    name: str
    price: float
    stock: int
    avg_rating: float
    rating_count: int
    description: str | None
    category_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


# тестовая схема для добавления новых товаров в бд
class NewProductData(BaseModel):
    name: str
    price: float
    stock: int
