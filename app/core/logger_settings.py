import json
import logging
import sys
from datetime import datetime, timezone

from app.core.context import get_request_id, get_user_id


class JSONFormatter(logging.Formatter):
    STANDART_KEYS = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "taskName",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
    }
    SENSITIVE_KEYS = {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "card_number",
    }

    def _mask_sensitive_data(self, data: any) -> any:
        if isinstance(data, dict):
            return {
                k: (
                    self._mask_sensitive_data(v)
                    if k not in self.SENSITIVE_KEYS
                    else "***"
                )
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        return data

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "level": record.levelname,
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = get_request_id()
        if request_id:
            log_obj["request_id"] = str(request_id)

        user_id = get_user_id()
        if user_id:
            log_obj["user_id"] = str(user_id)

        if record.exc_info:
            log_obj["stack_trace"] = self.formatException(record.exc_info)
            log_obj.update(
                {
                    "file": record.filename,
                    "line": record.lineno,
                    "function": record.funcName,
                    "module": record.module,
                }
            )

        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self.STANDART_KEYS and not k.startswith("_")
        }
        if extra:
            log_obj["extra"] = extra

        log_obj = self._mask_sensitive_data(log_obj)

        return json.dumps(log_obj, ensure_ascii=False, default=str)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(logging.INFO)

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.setLevel(logging.WARNING)
    uvicorn_access.propagate = False

    for name in ["sqlalchemy.engine", "sqlalchemy.pool"]:
        logger = logging.getLogger(name)
        logger.setLevel(logging.ERROR)
        logger.propagate = True

    if not root_logger.handlers:
        root_logger.addHandler(handler)

    for name in ["uvicorn", "uvicorn.error"]:
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
