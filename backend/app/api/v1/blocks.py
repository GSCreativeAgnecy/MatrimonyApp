from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.services.block_service import BlockService

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.get("", summary="List users I have blocked", response_model=ApiResponse[list[dict]])
async def list_blocks(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    service = BlockService(session)
    blocks = await service.blocked_users(user)
    return ApiResponse(data=[{"id": str(b.id), "blocked_user_id": str(b.blocked_id)} for b in blocks])


@router.post("/{user_id}", summary="Block a user", response_model=ApiResponse[dict])
async def block_user(
    user_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = BlockService(session)
    block = await service.block(user, user_id)
    await session.commit()
    return ApiResponse(data={"id": str(block.id), "blocked_user_id": str(user_id)})


@router.delete("/{user_id}", summary="Unblock a user", response_model=ApiResponse[dict])
async def unblock_user(
    user_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = BlockService(session)
    await service.unblock(user, user_id)
    await session.commit()
    return ApiResponse(data={"status": "unblocked"})
