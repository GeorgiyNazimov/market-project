from datetime import datetime, timedelta, timezone
from decimal import Decimal
from random import randint
from typing import List
from uuid import uuid4

from app.database.models import Product
from app.database.models.product_avg_rating import ProductAverageRating
from app.schemas.base import PaginationParams
from app.schemas.product import NewProductData, ProductUpdateData


def product_factory(
    name: str = "product_name",
    price: int | None = None,
    stock: int | None = None,
    product_rating_include: bool = False,
    **kwargs,
) -> Product:
    product_rating = None
    if product_rating_include:
        product_rating = product_rating_factory()
    return Product(
        id=kwargs.get("id", uuid4()),
        name=name,
        description=kwargs.get("description", "product_description"),
        price=price if price is not None else randint(1, 10000),
        stock=stock if stock is not None else randint(1, 10000),
        created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
        product_rating=product_rating,
    )


def product_rating_factory():
    return ProductAverageRating()


def new_product_data_factory(
    name: str = "product_name",
    description: str = "product_description",
    price: Decimal | None = None,
    stock: int | None = None,
):
    return NewProductData.model_validate(
        {
            "name": name,
            "description": description,
            "price": price if price is not None else Decimal(randint(1, 10000)),
            "stock": stock if stock is not None else randint(1, 10000),
        }
    )


def multiple_products_factory(count: int = 2) -> List[Product]:
    base_time = datetime.now(timezone.utc)
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


def product_update_data_factory(
    name: str | None = "updated_product_name",
    price: Decimal | None = None,
    stock: int | None = None,
    description: str | None = "updated_product_description",
) -> ProductUpdateData:
    return ProductUpdateData(
        name=name,
        price=price if price is not None else Decimal(randint(1, 10000)),
        stock=stock if stock is not None else randint(1, 10000),
        description=description,
    )
