from app.schemas.base import PaginationParams


def pagination_params_factory(
    sort_by: str = "created_at", cursor: str | None = None, limit: int = 10
) -> PaginationParams:
    return PaginationParams(sort_by=sort_by, cursor=cursor, limit=limit)
