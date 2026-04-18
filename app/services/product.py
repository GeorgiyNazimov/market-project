import base64
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, ConflictError, NotFoundError
from app.database.models.product import Product
from app.database.models.product_avg_rating import ProductAverageRating
from app.database.models.review import Review
from app.repositories.product import (
    create_product,
    create_product_review_repo,
    get_product_data_repo,
    get_product_list_repo,
    get_product_review_list_repo,
    get_review_by_user_and_product_repo,
    update_product_average_rating_repo,
)
from app.schemas.base import PaginationParams
from app.schemas.product import (
    NewProductData,
    NewReviewData,
    ProductData,
    ReviewData,
    ReviewDataList,
    ShortProductData,
    ShortProductDataList,
)
from app.schemas.user import UserTokenData

PRODUCT_SORT_CONFIG = {
    "created_at": (Product.created_at, datetime.fromisoformat, lambda p: p.created_at),
}

REVIEW_SORT_CONFIG = {
    "created_at": (Review.created_at, datetime.fromisoformat, lambda r: r.created_at),
}


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


async def get_product_list_serv(
    pagination_params: PaginationParams,
    session: AsyncSession,
) -> ShortProductDataList:
    sort_by = pagination_params.sort_by
    cursor = pagination_params.cursor
    limit = pagination_params.limit

    config = PRODUCT_SORT_CONFIG.get(sort_by)
    if not config:
        raise BadRequest(f"Sorting by {sort_by} is not supported")

    sort_field, parse_func, get_val = config
    last_value, last_id = decode_cursor(cursor, parse_func) if cursor else (None, None)

    product_list = await get_product_list_repo(
        sort_field, last_value, last_id, limit + 1, session
    )

    next_cursor = None
    # если мы забрали последние данные из таблицы, курсор не создаётся
    if len(product_list) > limit:
        product_list = product_list[:limit]
        last = product_list[-1]
        next_cursor = encode_cursor({"v": get_val(last), "i": last.id})

    products_data = [
        ShortProductData.model_validate(product) for product in product_list
    ]
    return ShortProductDataList(product_list=products_data, next_cursor=next_cursor)


async def get_product_serv(product_id: UUID, session: AsyncSession) -> ProductData:
    product = await get_product_data_repo(product_id, session)
    if product is None:
        raise NotFoundError(f"Product with id {product_id} not found")
    return ProductData.model_validate(product)


# тестовая функция для добавления новых товаров в бд
async def add_product_in_market(productInfo: NewProductData, session: AsyncSession):
    await create_product(productInfo, session)


async def create_product_review_serv(
    product_id: UUID,
    review_data: NewReviewData,
    token_data: UserTokenData,
    session: AsyncSession,
):
    existing = await get_review_by_user_and_product_repo(
        product_id, token_data.id, session
    )
    if existing:
        raise ConflictError("You already wrote review for this product")

    try:
        new_review = Review(
            text=review_data.text,
            product_rating=review_data.product_rating,
            product_id=product_id,
            user_id=token_data.id,
        )
        await create_product_review_repo(new_review, session)
        await session.flush()

        rating = review_data.product_rating
        await update_product_average_rating_repo(product_id, rating, session)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        sqlstate = getattr(e.orig, "sqlstate", None)
        if sqlstate == "23503":  # FK violation
            raise NotFoundError("Product not found") from e
        if sqlstate == "23505":  # unique violation
            raise ConflictError("You already wrote review for this product") from e
        raise


async def get_product_review_list_serv(
    product_id: UUID,
    pagination_params: PaginationParams,
    session: AsyncSession,
) -> ReviewDataList:
    sort_by = pagination_params.sort_by
    cursor = pagination_params.cursor
    limit = pagination_params.limit

    config = REVIEW_SORT_CONFIG.get(sort_by)
    if not config:
        raise BadRequest(f"Sorting by {sort_by} is not supported")

    sort_field, parse_func, get_val = config
    last_value, last_id = decode_cursor(cursor, parse_func) if cursor else (None, None)

    review_list = await get_product_review_list_repo(
        product_id, sort_field, last_value, last_id, limit + 1, session
    )
    review_list = [ReviewData.model_validate(review) for review in review_list]

    next_cursor = None
    if len(review_list) > limit:
        review_list = review_list[:limit]
        last = review_list[-1]
        next_cursor = encode_cursor({"v": get_val(last), "i": last.id})

    return ReviewDataList(review_list=review_list, next_cursor=next_cursor)
