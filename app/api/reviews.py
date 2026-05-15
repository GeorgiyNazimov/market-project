from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_session
from app.core.routing import LoggingRoute
from app.schemas.base import IdResponse
from app.schemas.review import ReviewUpdateData
from app.schemas.user import UserTokenData
from app.services.review import delete_review_serv, update_review_serv

app = APIRouter(prefix="/reviews", tags=["Reviews"], route_class=LoggingRoute)


@app.patch("/{review_id}")
async def update_review_handler(
    review_id: UUID,
    review_update_data: ReviewUpdateData,
    token_data: UserTokenData = Depends(RoleChecker(["user", "admin"])),
    session: AsyncSession = Depends(get_session),
):
    updated_id = await update_review_serv(
        review_id, review_update_data, token_data, session
    )
    return IdResponse(id=updated_id)


@app.delete("/{review_id}")
async def delete_review_handler(
    review_id: UUID,
    token_data: UserTokenData = Depends(RoleChecker(["user", "admin"])),
    session: AsyncSession = Depends(get_session),
):
    deleted_id = await delete_review_serv(review_id, token_data, session)
    return IdResponse(id=deleted_id)
