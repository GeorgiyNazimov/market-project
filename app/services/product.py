import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, ConflictError, NotFoundError
from app.database.models.product import Product
from app.repositories.product import (
    create_product_repo,
    delete_product_repo,
    get_product_by_name_repo,
    get_product_list_repo,
    get_product_repo,
    update_product_repo,
)
from app.schemas.base import PaginationParams
from app.schemas.product import (
    NewProductData,
    ProductData,
    ProductUpdateData,
    ShortProductData,
    ShortProductDataList,
)
from app.utils.logging import get_schema_diff
from app.utils.pagination import decode_cursor, encode_cursor

logger = logging.getLogger("service.product")

PRODUCT_SORT_CONFIG = {
    "created_at": (Product.created_at, datetime.fromisoformat, lambda p: p.created_at),
}


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


async def create_product_serv(product_data: NewProductData, session: AsyncSession):
    product_data.name = product_data.name.strip()
    exists = await get_product_by_name_repo(product_data.name, session)
    if exists:
        raise ConflictError("Product with this name already exists")

    new_product = Product(**product_data.model_dump())
    await create_product_repo(new_product, session)
    await session.commit()

    logger.info(
        "product_create_success",
        extra={
            "product_id": new_product.id,
            "product_name": new_product.name,
            "price": new_product.price,
            "stock": new_product.stock,
        },
    )
    return new_product.id


async def get_product_serv(product_id: UUID, session: AsyncSession) -> ProductData:
    product = await get_product_repo(product_id, session)
    if product is None:
        raise NotFoundError(f"Product with id {product_id} not found")
    return ProductData.model_validate(product)


async def update_product_serv(
    product_id: UUID, product_update_data: ProductUpdateData, session: AsyncSession
):
    product = await get_product_repo(product_id, session)
    if not product:
        raise NotFoundError("Product not found")

    old_snapshot = ProductUpdateData.model_validate(product)

    update_data = product_update_data.model_dump(exclude_unset=True)
    if not update_data:
        raise BadRequest("No data provided for update")

    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()
        duplicate = await get_product_by_name_repo(update_data["name"], session)
        if duplicate and duplicate.id != product_id:
            raise ConflictError(f"Product '{update_data['name']}' already exists")

    try:
        updated_product = await update_product_repo(product_id, update_data, session)
        if not updated_product:
            await session.rollback()
            raise NotFoundError("Product not found")

        new_snapshot = ProductUpdateData.model_validate(updated_product)

        changes = get_schema_diff(old_snapshot, new_snapshot)
        await session.commit()

        logger.info(
            "product_update_success", extra={"product_id": product_id, "diff": changes}
        )
        return updated_product.id
    except Exception:
        await session.rollback()
        raise


async def delete_product_serv(product_id: UUID, session: AsyncSession):
    try:
        deleted_id = await delete_product_repo(product_id, session)
        if deleted_id is None:
            await session.rollback()
            raise NotFoundError("Product not found")

        await session.commit()

        logger.info("product_delete_success", extra={"product_id": product_id})
        return deleted_id
    except Exception:
        await session.rollback()
        raise
