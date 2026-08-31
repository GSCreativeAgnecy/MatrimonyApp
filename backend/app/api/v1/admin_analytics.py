from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.db.models import User
from app.schemas.common import ApiResponse
from app.services.admin_analytics_service import AdminAnalyticsService, parse_range

router = APIRouter(prefix="/admin/analytics", tags=["admin", "analytics"])

can_read = require_permission("analytics.read")


def _range_params(
    range: str | None = Query(default=None, pattern="^(today|7d|30d|90d|custom)$"),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
) -> dict:
    return {"range": range, "from_": from_, "to": to}


@router.get("/users", summary="User analytics", response_model=ApiResponse[dict])
async def analytics_users(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[dict]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    return ApiResponse(data=await AdminAnalyticsService(session).analytics_users(parsed))


@router.get("/engagement", summary="Engagement analytics", response_model=ApiResponse[dict])
async def analytics_engagement(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[dict]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    return ApiResponse(data=await AdminAnalyticsService(session).analytics_engagement(parsed))


@router.get("/matching", summary="Matching funnel analytics", response_model=ApiResponse[dict])
async def analytics_matching(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[dict]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    return ApiResponse(data=await AdminAnalyticsService(session).analytics_matching(parsed))


@router.get("/revenue", summary="Revenue analytics", response_model=ApiResponse[dict])
async def analytics_revenue(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[dict]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    return ApiResponse(data=await AdminAnalyticsService(session).analytics_revenue(parsed))


@router.get("/moderation", summary="Moderation analytics", response_model=ApiResponse[dict])
async def analytics_moderation(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[dict]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    return ApiResponse(data=await AdminAnalyticsService(session).analytics_moderation(parsed))
