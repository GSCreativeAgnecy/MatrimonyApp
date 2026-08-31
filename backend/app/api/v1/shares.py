from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.monetization import ProfileShareCreate, ProfileShareResponse
from app.services.share_service import ShareService

router = APIRouter(prefix="/profile-shares", tags=["profile-sharing"])


@router.post("", summary="Share my profile with another user", response_model=ApiResponse[ProfileShareResponse])
async def create_share(
    body: ProfileShareCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[ProfileShareResponse]:
    service = ShareService(session)
    share = await service.create(
        user,
        UUID(body.shared_with_user_id),
        permission=body.permission,
        expires_in_days=body.expires_in_days,
    )
    await session.commit()
    return ApiResponse(data=ProfileShareResponse.model_validate(share))


@router.get("", summary="List my outgoing profile shares", response_model=ApiResponse[list[ProfileShareResponse]])
async def list_shares(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[ProfileShareResponse]]:
    service = ShareService(session)
    shares = await service.list_for_owner(user)
    return ApiResponse(data=[ProfileShareResponse.model_validate(s) for s in shares])


@router.delete("/{share_id}", summary="Revoke a profile share", response_model=ApiResponse[dict])
async def revoke_share(
    share_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = ShareService(session)
    await service.revoke(user, share_id)
    await session.commit()
    return ApiResponse(data={"status": "revoked"})
