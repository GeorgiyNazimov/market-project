from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        content = {
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            }
        }

        if exc.payload:
            content["error"]["details"] = exc.payload

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=exc.headers or {},
        )
