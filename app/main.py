from fastapi import FastAPI
from uvicorn import run
from sqladmin import Admin

from app.admin.admin import authentication_backend
from app.admin.views import admin_views
from app.api import list_of_routers
from app.database.connection.session import _engine
from app.config import Settings, get_settings
from app.core.exception_handler import register_exception_handlers


def bind_routes(application: FastAPI, setting: Settings) -> None:
    for router in list_of_routers:
        application.include_router(router, prefix=setting.PATH_PREFIX)

def add_views(admin: Admin, admin_views):
    for view in admin_views:
        admin.add_view(view)

def get_app() -> FastAPI:
    description = ""

    application = FastAPI(
        docs_url="/api/v1/swagger",
        openapi_url="/api/v1/openapi",
        version="1.0.0",
        title="MarketProject",
        description=description,
    )
    
    admin = Admin(
        app=application, 
        engine=_engine, 
        authentication_backend=authentication_backend,
        base_url="/admin",          # Адрес админки
        title="Market Admin",       # Заголовок в браузере
        templates_dir="templates",  # Если хочешь свои кастомные шаблоны
    )
    add_views(admin, admin_views)

    register_exception_handlers(application)
    
    settings = get_settings()
    bind_routes(application, settings)
    application.state.settings = settings
    return application


app = get_app()


if __name__ == "__main__":
    settings_for_application = get_settings()
    run(
        "main:app",
        port=settings_for_application.BACKEND_PORT,
        reload=True,
        reload_dirs=["app"],
        log_level="debug",
        host=settings_for_application.BACKEND_HOST,
    )
