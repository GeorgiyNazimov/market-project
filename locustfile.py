from locust import HttpUser, task, between
from uuid import uuid4
from app.config.default import get_settings

settings = get_settings()


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        """Каждый пользователь регистрируется и логинится"""
        self.email = f"user_{uuid4().hex}@test.com"
        self.password = "string"

        # Регистрация
        self.client.post(
            f"{settings.PATH_PREFIX}/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "first_name": "Test",
                "last_name": "User",
            },
        )

        # Логин
        response = self.client.post(
            f"{settings.PATH_PREFIX}/auth/token",
            data={"username": self.email, "password": self.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            access_token = response.json().get("access_token")
            self.auth_headers = {"Authorization": f"Bearer {access_token}"}
        else:
            self.auth_headers = {}

    @task
    def get_my_info(self):
        """Запрашивает данные текущего пользователя"""
        self.client.get(
            f"{settings.PATH_PREFIX}/auth/users/me", headers=self.auth_headers
        )
