import base64
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID


def encode_cursor(cursor_data: Dict[str, Any]) -> str:
    def json_serial(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (UUID, Decimal)):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    json_str = json.dumps(cursor_data, ensure_ascii=False, default=json_serial)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor_str: str, parse_func) -> Dict[str, Any]:
    try:
        decoded_bytes = base64.urlsafe_b64decode(cursor_str.encode())
        data = json.loads(decoded_bytes.decode())

        raw_value = parse_func(data["v"]) if data.get("v") else None
        raw_id = UUID(data["i"]) if data.get("i") else None

        return raw_value, raw_id
    except Exception:
        return None, None
