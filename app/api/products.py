from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.default import Settings, get_settings
from app.database.connection.session import get_session
from app.database.models.user import User
from app.schemas.products import ProductData, ShortProductDataList
from app.services.auth import get_current_user
from app.services.products import add_product_in_cart, get_product_list, get_product_data

app = APIRouter(prefix="/product", tags=["Products"])

@app.get("/")
async def get_product_list_handler(
        session: AsyncSession = Depends(get_session)
) -> ShortProductDataList:
    product_list = await get_product_list(session)
    return product_list

@app.get("/{product_id}")
async def get_product_data_handler(
    product_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> ProductData:
    product_data = await get_product_data(product_id, session)
    return product_data

@app.post("/{product_id}/cart")
async def add_product_in_cart_handler(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await add_product_in_cart(product_id, current_user, session)
    return result