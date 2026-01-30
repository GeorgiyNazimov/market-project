from typing import List
from app.database.models import Product
from uuid import uuid4
from random import randint
from datetime import datetime, timedelta

from app.schemas.products import NewProductData

def product_factory(
    name='product_name',
    description='product_description',
    price=randint(1, 10000),
    stock=randint(1, 10000),
) -> Product:
    return Product(
        id=uuid4(),
        name=name,
        description=description,
        price=price,
        stock=stock,
        created_at=datetime.utcnow()
    )

def new_product_data_factory(
    name='product_name',
    price=randint(1, 10000),
    stock=randint(1, 10000),
):
    return NewProductData.model_validate({
        "name":name,
        "price":price,
        "stock":stock,
    })

def multiple_products_factory(count: int=2) -> List[Product]:
    base_time = datetime.utcnow()
    return [Product(
        id=uuid4(),
        name='product_name',
        description='product_description',
        price=randint(1, 10000),
        stock=randint(1, 10000),
        created_at=base_time + timedelta(i)
    ) for i in range(count)]