from app.api.auth import app as auth_router
from app.api.products import app as product_router
from app.api.cart import app as cart_router
from app.api.review import app as review_router


list_of_routers = [
    auth_router,
    product_router,
    cart_router,
    review_router,
]

__all__ = [
    "list_of_routers",
]
