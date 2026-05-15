import logging
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

from app.core.exceptions import AppException

logger = logging.getLogger("api.access")


class LoggingRoute(APIRoute):
    async def _get_request_body(self, request: Request) -> any:
        body = await request.body()
        if not body:
            return None

        try:
            return await request.json()
        except Exception:
            return body.decode(errors="replace").replace("\n", " ").replace("\r", "")

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.perf_counter()

            client_ip = request.headers.get(
                "x-forwarded-for", request.client.host if request.client else "unknown"
            )
            extra = {
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
            }

            try:
                response = await original_route_handler(request)
                process_time = round((time.perf_counter() - start_time) * 1000, 2)
                extra.update(
                    {
                        "status_code": response.status_code,
                        "process_time_ms": process_time,
                    }
                )

                if response.status_code >= 400:
                    extra["request_body"] = await self._get_request_body(request)
                    logger.warning("http_request_warning", extra=extra)
                else:
                    logger.info("http_request_completed", extra=extra)
                return response

            except Exception as exc:
                is_app_exc = isinstance(exc, AppException)
                status_code = exc.status_code if is_app_exc else 500
                process_time = round((time.perf_counter() - start_time) * 1000, 2)

                extra.update(
                    {"status_code": status_code, "process_time_ms": process_time}
                )

                need_details = (not is_app_exc) or exc.log_it

                if need_details:
                    extra.update(
                        {
                            "request_body": await self._get_request_body(request),
                            "error_detail": exc.message if is_app_exc else str(exc),
                        }
                    )

                if not is_app_exc:
                    logger.exception("http_request_crashed", extra=extra)
                elif exc.log_it:
                    logger.warning("http_business_error", extra=extra)
                else:
                    logger.info("http_request_completed", extra=extra)

                raise exc

        return custom_route_handler
