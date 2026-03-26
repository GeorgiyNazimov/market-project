from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.database.models.order_item import OrderItem
from app.database.models.order import Order
from app.database.models.product import Product
from app.database.models.user import User
from tests.factories.products import product_factory
from tests.factories.users import user_factory


def order_factory(user: User | None = None, **kwargs) -> Order:
    target_user = user or user_factory()

    return Order(
        id=kwargs.get("id", uuid4()),
        user=target_user,
        status=kwargs.get("status", "pending"),
        total_price=kwargs.get("total_price", Decimal(0)),
        created_at=datetime.utcnow(),
    )


def order_item_factory(
    order: Order | None = None, product: Product | None = None, **kwargs
) -> OrderItem:

    target_product = product or product_factory()
    target_order = order or order_factory()

    return OrderItem(
        id=kwargs.get("id", uuid4()),
        order=target_order,
        product=target_product,
        quantity=kwargs.get("quantity", 1),
        price=target_product.price,
    )
