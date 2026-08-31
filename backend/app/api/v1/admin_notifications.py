from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.db.models import NotificationCampaign, User
from app.schemas.admin import CampaignCreate, CampaignRow
from app.schemas.common import ApiResponse
from app.services.notification_campaign_service import NotificationCampaignService, defer_seconds_for
from app.workers.enqueue import enqueue_notification_campaign

router = APIRouter(prefix="/admin/notifications", tags=["admin", "notifications"])

can_send = require_permission("notifications.send")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.post(
    "/campaign", summary="Create a notification campaign (processed by ARQ)", response_model=ApiResponse[CampaignRow]
)
async def create_campaign(
    payload: CampaignCreate,
    request: Request,
    admin: User = Depends(can_send),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[CampaignRow]:
    service = NotificationCampaignService(session)
    campaign = await service.create(admin, payload.model_dump())
    await session.commit()

    defer = defer_seconds_for(payload.schedule_at)
    await enqueue_notification_campaign(str(campaign.id), defer_seconds=defer if defer else None)
    return ApiResponse(data=CampaignRow.model_validate(campaign))


@router.get("/campaigns", summary="List notification campaigns", response_model=ApiResponse[list[CampaignRow]])
async def list_campaigns(
    admin: User = Depends(can_send),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[CampaignRow]]:
    from sqlalchemy import func

    total = int((await session.execute(select(func.count()).select_from(NotificationCampaign))).scalar_one())
    rows = list(
        (
            await session.execute(
                select(NotificationCampaign)
                .order_by(NotificationCampaign.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return ApiResponse(data=[CampaignRow.model_validate(c) for c in rows], meta=_meta(total, limit, offset))
