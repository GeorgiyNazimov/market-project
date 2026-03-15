from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrderItemRead(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj):
        data = super().model_validate(obj)
        if hasattr(obj, "product"):
            data.product_name = obj.product.name
        return data


class OrderRead(BaseModel):
    id: UUID
    status: str
    items: list[OrderItemRead]
    total_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListRead(BaseModel):
    orders: list[OrderRead]


class OrderCreate(BaseModel):
    cart_item_ids: list[UUID]
