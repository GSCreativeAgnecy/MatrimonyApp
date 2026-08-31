from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.discovery import RecommendationFeed
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", summary="Get my recommendation feed", response_model=ApiResponse[RecommendationFeed])
async def get_feed(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> ApiResponse[RecommendationFeed]:
    service = RecommendationService(session)
    feed = await service.build_feed(user, limit=limit, cursor=cursor)
    return ApiResponse(
        data=RecommendationFeed(
            items=feed["items"],
            next_cursor=feed["next_cursor"],
            has_more=feed["has_more"],
        )
    )
