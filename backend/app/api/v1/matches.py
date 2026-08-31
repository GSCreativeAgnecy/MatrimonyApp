from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.repositories.profile_repo import ProfileRepository
from app.schemas.common import ApiResponse
from app.schemas.discovery import MatchResponse
from app.services.match_service import MatchService
from app.services.profile_service import _age

router = APIRouter(prefix="/matches", tags=["matches"])


async def _serialize(session: AsyncSession, user: User) -> list[MatchResponse]:
    service = MatchService(session)
    matches = await service.list_for(user)
    result = []
    photos = await ProfileRepository(session).get_primary_photos(
        [m.user1_id if m.user1_id != user.id else m.user2_id for m in matches]
    )
    for m in matches:
        other_id = m.user2_id if m.user1_id == user.id else m.user1_id
        profile = await ProfileRepository(session).get_by_user(other_id)
        result.append(
            MatchResponse(
                id=str(m.id),
                user_id=str(other_id),
                first_name=profile.first_name if profile else None,
                age=_age(profile.date_of_birth) if profile else None,
                city=profile.city if profile else None,
                state=profile.state if profile else None,
                country=profile.country if profile else None,
                occupation=profile.occupation if profile else None,
                profile_photo=photos.get(other_id),
                status=m.status.value,
                matched_at=m.matched_at,
            )
        )
    return result


@router.get("", summary="List my active matches", response_model=ApiResponse[list[MatchResponse]])
async def list_matches(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[MatchResponse]]:
    data = await _serialize(session, user)
    return ApiResponse(data=data)


@router.delete("/{match_id}", summary="Unmatch", response_model=ApiResponse[dict])
async def unmatch(
    match_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = MatchService(session)
    await service.unmatch(user, match_id)
    await session.commit()
    return ApiResponse(data={"status": "unmatched"})
