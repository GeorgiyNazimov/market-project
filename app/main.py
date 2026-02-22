from fastapi import FastAPI
from uvicorn import run

from app.api import list_of_routers
from app.config import Settings, get_settings
from app.core.exception_handler import register_exception_handlers


def bind_routes(application: FastAPI, setting: Settings) -> None:
    for router in list_of_routers:
        application.include_router(router, prefix=setting.PATH_PREFIX)


def get_app() -> FastAPI:
    description = ""

    application = FastAPI(
        docs_url="/api/v1/swagger",
        openapi_url="/api/v1/openapi",
        version="1.0.0",
        title="MarketProject",
        description=description,
    )

    settings = get_settings()
    bind_routes(application, settings)
    application.state.settings = settings
    return application


app = get_app()
register_exception_handlers(app)

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
