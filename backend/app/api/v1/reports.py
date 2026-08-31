from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.discovery import ReportCreate, ReportResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", summary="Report a user", response_model=ApiResponse[ReportResponse])
async def create_report(
    body: ReportCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[ReportResponse]:
    service = ReportService(session)
    report = await service.create(user, UUID(body.reported_user_id), body.reason, body.description)
    await session.commit()
    return ApiResponse(data=ReportResponse.model_validate(report))
