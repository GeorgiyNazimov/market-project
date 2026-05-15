import contextvars

from sqlalchemy import UUID

_request_id_var = contextvars.ContextVar(
    "request_id",
    default=None,
)
_user_id_ctx = contextvars.ContextVar("user_id", default=None)


def set_request_id(request_id: str) -> contextvars.Token:
    return _request_id_var.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    _request_id_var.reset(token)


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_user_id(user_id: UUID):
    _user_id_ctx.set(user_id)


def reset_user_id(token: contextvars.Token):
    _user_id_ctx.reset(token)


def get_user_id():
    return _user_id_ctx.get()
