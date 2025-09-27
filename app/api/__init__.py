from app.api.auth import app as auth_router


list_of_routers = [
    auth_router,
]

__all__ = [
    "list_of_routers",
]
