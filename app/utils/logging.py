from typing import Any

from pydantic import BaseModel


def get_schema_diff(old_snapshot: Any, new_snapshot: Any) -> dict:
    changes = {}
    old_dict = (
        old_snapshot.model_dump()
        if isinstance(old_snapshot, BaseModel)
        else old_snapshot
    )
    new_dict = (
        new_snapshot.model_dump()
        if isinstance(new_snapshot, BaseModel)
        else new_snapshot
    )

    for key, new_val in new_dict.items():
        old_val = old_dict.get(key)

        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}

    return changes
