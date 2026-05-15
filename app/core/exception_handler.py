from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.context import get_request_id
from app.core.exceptions import AppException


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return build_error_response(exc)

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        internal_exc = AppException(
            message="An unexpected system error occurred",
        )
        return build_error_response(internal_exc)


def build_error_response(exc: AppException):
    request_id = get_request_id()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id,
                **({"details": exc.payload} if exc.payload else {}),
            }
        },
        headers={
            **(exc.headers or {}),
            "X-Request-ID": request_id or "",
        },
    )
