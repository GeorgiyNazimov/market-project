from datetime import datetime, timedelta
from random import randint
from typing import List
from uuid import uuid4

from app.database.models import Product
from app.schemas.base import PaginationParams
from app.schemas.product import NewProductData


def product_factory(
    name: str = "product_name",
    price: int | None = None,
    stock: int | None = None,
    **kwargs,
) -> Product:
    return Product(
        id=kwargs.get("id", uuid4()),
        name=name,
        description=kwargs.get("description", "product_description"),
        price=price if price is not None else randint(1, 10000),
        stock=stock if stock is not None else randint(1, 10000),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )


def new_product_data_factory(
    name: str = "product_name",
    price: int | None = None,
    stock: int | None = None,
):
    return NewProductData.model_validate(
        {
            "name": name,
            "price": price if price is not None else randint(1, 10000),
            "stock": stock if stock is not None else randint(1, 10000),
        }
    )


def multiple_products_factory(count: int = 2) -> List[Product]:
    base_time = datetime.utcnow()
    return [
        Product(
            id=uuid4(),
            name="product_name",
            description="product_description",
            price=randint(1, 10000),
            stock=randint(1, 10000),
            created_at=base_time + timedelta(i),
        )
        for i in range(count)
    ]


def pagination_params_factory(
    sort_by: str = "created_at",
    cursor: str | None = None,
    limit: int = 10
) -> PaginationParams:
    return PaginationParams(
        sort_by=sort_by,
        cursor=cursor,
        limit=limit
    )