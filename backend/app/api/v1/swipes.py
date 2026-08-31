from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.discovery import SwipeCreate, SwipeResponse
from app.services.swipe_service import SwipeService

router = APIRouter(prefix="/swipes", tags=["swipes"])


@router.post("", summary="Like / pass / super-like a user", response_model=ApiResponse[SwipeResponse])
async def create_swipe(
    body: SwipeCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[SwipeResponse]:
    service = SwipeService(session)
    result = await service.swipe(user, UUID(body.target_user_id), body.action.value)
    await session.commit()
    return ApiResponse(data=SwipeResponse(**result))
