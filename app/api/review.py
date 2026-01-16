from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection.session import get_session
from app.database.models.user import User
from app.schemas.review import NewReviewData, ReviewDataList
from app.services.auth import get_current_user
from app.services.review import create_product_review, get_product_reviews_list

app = APIRouter(prefix="/reviews", tags=["Reviews"])

@app.get("/{product_id}")
async def get_product_reviews_list_handler(
    product_id: UUID,
    created_at_cursor: datetime | None = Query(None),
    id_cursor: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
) -> ReviewDataList:
    reviews_list = await get_product_reviews_list(product_id, created_at_cursor, id_cursor, limit, session)
    return reviews_list

@app.post("/{product_id}/create_review")
async def create_product_review_handler(
    product_id: UUID,
    reviewData: NewReviewData,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await create_product_review(product_id, reviewData, current_user, session)
