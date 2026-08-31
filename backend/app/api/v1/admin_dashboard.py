from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_any_permission
from app.db.models import User
from app.schemas.admin import (
    ActionCenterItem,
    DashboardSummary,
    EngagementBucket,
    ModerationBucket,
    RecentActivityItem,
    RevenueBucket,
    TimeBucket,
)
from app.schemas.common import ApiResponse
from app.services.admin_analytics_service import AdminAnalyticsService, parse_range

router = APIRouter(prefix="/admin/dashboard", tags=["admin", "dashboard"])

read_dashboard = require_any_permission("analytics.read", "users.read", "reports.read")


@router.get("/summary", summary="Dashboard summary counts", response_model=ApiResponse[DashboardSummary])
async def summary(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[DashboardSummary]:
    data = await AdminAnalyticsService(session).summary()
    return ApiResponse(data=DashboardSummary(**data))


@router.get(
    "/action-center",
    summary="Items needing administrator attention",
    response_model=ApiResponse[list[ActionCenterItem]],
)
async def action_center(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[ActionCenterItem]]:
    data = await AdminAnalyticsService(session).action_center()
    return ApiResponse(data=[ActionCenterItem(**item) for item in data])


@router.get("/recent-activity", summary="Latest audit events", response_model=ApiResponse[list[RecentActivityItem]])
async def recent_activity(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[list[RecentActivityItem]]:
    data = await AdminAnalyticsService(session).recent_activity(limit=limit)
    return ApiResponse(data=[RecentActivityItem(**item) for item in data])


def _range_params(
    range: str | None = Query(default=None, pattern="^(today|7d|30d|90d|custom)$"),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
) -> dict:
    return {"range": range, "from_": from_, "to": to}


@router.get("/user-growth", summary="User registrations over time", response_model=ApiResponse[list[TimeBucket]])
async def user_growth(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[list[TimeBucket]]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    data = await AdminAnalyticsService(session).user_growth(parsed)
    return ApiResponse(data=[TimeBucket(**item) for item in data], meta={"granularity": parsed.granularity})


@router.get(
    "/engagement",
    summary="Swipes/likes/matches/messages over time",
    response_model=ApiResponse[list[EngagementBucket]],
)
async def engagement(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[list[EngagementBucket]]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    data = await AdminAnalyticsService(session).engagement(parsed)
    return ApiResponse(data=[EngagementBucket(**item) for item in data], meta={"granularity": parsed.granularity})


@router.get("/revenue", summary="Revenue over time", response_model=ApiResponse[list[RevenueBucket]])
async def revenue(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[list[RevenueBucket]]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    data = await AdminAnalyticsService(session).revenue(parsed)
    return ApiResponse(data=[RevenueBucket(**item) for item in data], meta={"granularity": parsed.granularity})


@router.get("/moderation", summary="Moderation activity over time", response_model=ApiResponse[list[ModerationBucket]])
async def moderation(
    admin: User = Depends(read_dashboard),
    session: AsyncSession = Depends(get_session),
    rng: dict = Depends(_range_params),
) -> ApiResponse[list[ModerationBucket]]:
    parsed = parse_range(rng["range"], from_=rng["from_"], to=rng["to"])
    data = await AdminAnalyticsService(session).moderation(parsed)
    return ApiResponse(data=[ModerationBucket(**item) for item in data], meta={"granularity": parsed.granularity})
