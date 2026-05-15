import uuid

from fastapi import Request

from app.core.context import reset_request_id, set_request_id


async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

    token = set_request_id(request_id)

    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
    finally:
        reset_request_id(token)
