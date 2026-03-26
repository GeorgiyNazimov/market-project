from datetime import datetime
from uuid import UUID, uuid4

from app.database.models.cart import Cart
from app.database.models.cart_item import CartItem
from app.database.models.product import Product
from app.database.models.user import User
from app.schemas.cart import UpdateCartItemData
from tests.factories.products import product_factory
from tests.factories.users import user_factory


def cart_factory(user: User | None = None, **kwargs) -> Cart:
    target_user = user or user_factory()
    
    return Cart(
        id=kwargs.get("id", uuid4()),
        user=target_user,
        total_items=kwargs.get("total_items", 0),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )


def cart_item_factory(
    cart: Cart | None = None, 
    product: Product | None = None, 
    **kwargs
) -> CartItem:
    target_product = product or product_factory()
    target_cart = cart or cart_factory()

    return CartItem(
        id=kwargs.get("id", uuid4()),
        cart=target_cart,
        product=target_product,
        quantity=kwargs.get("quantity", 1),
    )


def update_cart_item_data_factory(
    cart_item_id: UUID | None = None, new_quantity: int = 1
) -> UpdateCartItemData:
    return UpdateCartItemData(
        cart_item_id=cart_item_id or uuid4(), new_quantity=new_quantity
    )
