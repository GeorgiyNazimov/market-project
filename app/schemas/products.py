from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ShortProductData(BaseModel):
    id: UUID
    name: str
    price: float
    stock: int
    category_id: UUID | None

    model_config = ConfigDict(from_attributes=True)

class ShortProductDataList(BaseModel):
    product_list: List[ShortProductData]

class ProductData(BaseModel):
    id: UUID
    name: str
    price: float
    stock: int
    description: str | None
    category_id: UUID | None

    model_config = ConfigDict(from_attributes=True)
