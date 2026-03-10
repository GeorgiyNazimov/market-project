from app.api.dependencies import get_session
from contextlib import asynccontextmanager
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.repositories.auth import get_user_from_db_by_email
from app.services.auth import verify_password


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        async with asynccontextmanager(get_session)() as session:
            user = await get_user_from_db_by_email(email, session)
            if not user:
                return False
            if not verify_password(password, user.password_hash):
                return False
            if not user.role == "admin":
                return False
        
        request.session.update({"token": "some-secret-token"})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

authentication_backend = AdminAuth(secret_key="very-secret-key")