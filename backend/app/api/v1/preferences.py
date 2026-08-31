from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.preference import PartnerPreferenceResponse, PartnerPreferenceUpdate
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", summary="Get my partner preferences", response_model=ApiResponse[PartnerPreferenceResponse])
async def get_preferences(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PartnerPreferenceResponse]:
    service = PreferenceService(session)
    data = await service.serialize(user.id)
    return ApiResponse(data=PartnerPreferenceResponse(**data))


@router.put("", summary="Replace my partner preferences", response_model=ApiResponse[PartnerPreferenceResponse])
async def put_preferences(
    body: PartnerPreferenceUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PartnerPreferenceResponse]:
    service = PreferenceService(session)
    payload = body.model_dump(exclude_unset=True)
    await service.update(user.id, payload)
    await session.commit()
    data = await service.serialize(user.id)
    return ApiResponse(data=PartnerPreferenceResponse(**data))
