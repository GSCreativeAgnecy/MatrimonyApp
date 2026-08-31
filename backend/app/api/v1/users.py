from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.errors import ForbiddenError
from app.db.models import User
from app.repositories.moderation_repo import BlockRepository
from app.repositories.profile_repo import ProfileRepository
from app.schemas.common import ApiResponse
from app.schemas.profile import MatchedProfileResponse, PublicProfileResponse
from app.services.match_service import MatchService
from app.services.profile_service import ProfileService, distance_km
from app.services.storage import build_storage

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{user_id}", summary="View another user's profile", response_model=ApiResponse[PublicProfileResponse])
async def get_profile(
    user_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PublicProfileResponse]:
    service = ProfileService(session)
    target = await service.get_target_user(user_id)

    if await BlockRepository(session).get_pair(user.id, user_id) or await BlockRepository(session).get_pair(
        user_id, user.id
    ):
        raise ForbiddenError("This profile is not available", code="BLOCKED")

    profile = await ProfileRepository(session).get_by_user(user_id)
    if profile is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Profile not found", code="PROFILE_NOT_FOUND")

    matched = await MatchService(session).get_active_between(user.id, user_id) is not None
    viewer_profile = await service.get_own(user)

    viewer_lat, viewer_lng = viewer_profile.location_lat, viewer_profile.location_lng
    dist = distance_km(viewer_lat, viewer_lng, profile.location_lat, profile.location_lng)

    storage = build_storage()
    photo_key = await ProfileRepository(session).get_profile_photo_url(user_id)
    photo_url = await storage.presigned_download_url(photo_key) if photo_key else None

    resp = await service.serialize_public(
        user, target, profile, matched=matched, distance_to_viewer=dist, photo_url=photo_url
    )
    if matched:
        return ApiResponse(data=MatchedProfileResponse(**resp.model_dump()))
    return ApiResponse(data=resp)


@router.get(
    "/{user_id}/contact",
    summary="Unlock contact details (matches / shared access)",
    response_model=ApiResponse[MatchedProfileResponse],
)
async def get_contact_details(
    user_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[MatchedProfileResponse]:
    service = ProfileService(session)
    target = await service.get_target_user(user_id)
    profile = await ProfileRepository(session).get_by_user(user_id)
    if profile is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Profile not found", code="PROFILE_NOT_FOUND")

    match = await MatchService(session).get_active_between(user.id, user_id)
    if match is None:
        raise ForbiddenError("Contact details are available only for matches", code="NOT_MATCHED")

    resp = await service.serialize_public(user, target, profile, matched=True)
    return ApiResponse(data=MatchedProfileResponse(**resp.model_dump()))
