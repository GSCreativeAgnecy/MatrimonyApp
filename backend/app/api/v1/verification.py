from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.monetization import (
    JobVerificationCheckoutResponse,
    JobVerificationCreate,
    JobVerificationResponse,
)
from app.services.verification_service import VerificationService

router = APIRouter(prefix="/verifications", tags=["verifications"])


@router.post(
    "/job",
    summary="Submit a paid job verification request",
    response_model=ApiResponse[JobVerificationCheckoutResponse],
)
async def submit_job_verification(
    body: JobVerificationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[JobVerificationCheckoutResponse]:
    service = VerificationService(session)
    data = await service.submit(user, body.model_dump())
    await session.commit()
    return ApiResponse(data=JobVerificationCheckoutResponse(**data))


@router.get("", summary="List my verification requests", response_model=ApiResponse[list[JobVerificationResponse]])
async def list_my_verifications(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[JobVerificationResponse]]:
    service = VerificationService(session)
    verifications = await service.list_mine(user.id)
    return ApiResponse(data=[JobVerificationResponse.model_validate(v) for v in verifications])
