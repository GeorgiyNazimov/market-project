from app.api.auth import app as auth_router
from app.api.products import app as product_router


list_of_routers = [
    auth_router,
    product_router,
]

__all__ = [
    "list_of_routers",
]
