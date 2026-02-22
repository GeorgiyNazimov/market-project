from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NextCursorData(BaseModel):
    created_at: datetime
    id: UUID


class ShortProductRatingData(BaseModel):
    avg_rating: float
    rating_count: int

    model_config = ConfigDict(from_attributes=True)


class ShortProductData(BaseModel):
    id: UUID
    name: str
    price: float
    stock: int
    category_id: UUID | None
    created_at: datetime
    product_rating: ShortProductRatingData | None

    model_config = ConfigDict(from_attributes=True)


class ShortProductDataList(BaseModel):
    product_list: List[ShortProductData]
    next_cursor: NextCursorData


class ProductRatingData(BaseModel):
    avg_rating: float
    rating_count: int
    rating_1_count: int
    rating_2_count: int
    rating_3_count: int
    rating_4_count: int
    rating_5_count: int

    model_config = ConfigDict(from_attributes=True)


class ProductData(BaseModel):
    id: UUID
    name: str
    price: float
    stock: int
    product_rating: ProductRatingData | None
    description: str | None
    category_id: UUID | None

    model_config = ConfigDict(from_attributes=True)


# тестовая схема для добавления новых товаров в бд
class NewProductData(BaseModel):
    name: str
    price: float
    stock: int
