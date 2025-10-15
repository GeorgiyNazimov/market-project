from decimal import Decimal
from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CartItemData(BaseModel):
    id: UUID
    name: str
    price: Decimal
    quantity: int
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)

class CartItemList(BaseModel):
    cart_items: List[CartItemData]

class UpdateCartItemData(BaseModel):
    cart_item_id: UUID
    new_quantity: int

class NewCartItemData(BaseModel):
    product_id: UUID
    cart_id: UUID
    id: UUID
    quantity: int

    model_config = ConfigDict(from_attributes=True)