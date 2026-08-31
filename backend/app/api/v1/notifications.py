from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.discovery import NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", summary="List my notifications", response_model=ApiResponse[list[NotificationResponse]])
async def list_notifications(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[NotificationResponse]]:
    service = NotificationService(session)
    notifications = await service.list_for_user(user.id, limit=limit, offset=offset)
    return ApiResponse(data=[NotificationResponse.model_validate(n) for n in notifications])


@router.get("/unread-count", summary="Unread notification count", response_model=ApiResponse[dict])
async def unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = NotificationService(session)
    return ApiResponse(data={"count": await service.unread_count(user.id)})


@router.post("/{notification_id}/read", summary="Mark one notification as read", response_model=ApiResponse[dict])
async def mark_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = NotificationService(session)
    await service.mark_read(user.id, notification_id)
    await session.commit()
    return ApiResponse(data={"status": "read"})


@router.post("/read-all", summary="Mark all notifications as read", response_model=ApiResponse[dict])
async def mark_all_read(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = NotificationService(session)
    count = await service.mark_all_read(user.id)
    await session.commit()
    return ApiResponse(data={"status": "read", "count": count})
