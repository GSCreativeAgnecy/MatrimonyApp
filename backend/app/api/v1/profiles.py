from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.repositories.user_repo import UserRepository
from app.schemas.common import ApiResponse
from app.schemas.profile import (
    OwnProfileResponse,
    PrivacySettingsResponse,
    PrivacySettingsUpdate,
    ProfileCreate,
    ProfileUpdate,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


async def _own_payload(session: AsyncSession, user: User) -> dict:
    service = ProfileService(session)
    profile = await service.get_own(user)
    privacy = await UserRepository(session).get_privacy(user.id)
    from app.services.photo_service import PhotoService

    photos = await PhotoService(session).list(user)
    profile_photo = next((p.url for p in photos if p.is_profile_photo), None)
    payload = {
        "id": str(profile.id),
        "user_id": str(user.id),
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "gender": profile.gender.value if profile.gender else None,
        "bio": profile.bio,
        "intent": profile.intent.value if profile.intent else None,
        "marital_status": profile.marital_status.value if profile.marital_status else None,
        "height_cm": profile.height_cm,
        "body_type": profile.body_type.value if profile.body_type else None,
        "complexion": profile.complexion.value if profile.complexion else None,
        "physical_status": profile.physical_status.value if profile.physical_status else None,
        "diet": profile.diet.value if profile.diet else None,
        "drinking": profile.drinking.value if profile.drinking else None,
        "smoking": profile.smoking.value if profile.smoking else None,
        "mother_tongue": profile.mother_tongue,
        "preferred_language": profile.preferred_language,
        "religion": profile.religion,
        "caste": profile.caste,
        "sub_caste": profile.sub_caste,
        "education": profile.education,
        "college": profile.college,
        "field_of_study": profile.field_of_study,
        "graduation_year": profile.graduation_year,
        "employment_status": profile.employment_status.value if profile.employment_status else None,
        "occupation": profile.occupation,
        "job_title": profile.job_title,
        "workplace": profile.workplace,
        "industry": profile.industry,
        "annual_income": float(profile.annual_income) if profile.annual_income is not None else None,
        "income_currency": profile.income_currency,
        "country": profile.country,
        "state": profile.state,
        "city": profile.city,
        "hometown": profile.hometown,
        "profile_created_by": profile.profile_created_by.value if profile.profile_created_by else None,
        "location_lat": profile.location_lat,
        "location_lng": profile.location_lng,
        "location_updated_at": profile.location_updated_at.isoformat() if profile.location_updated_at else None,
        "privacy": PrivacySettingsResponse.model_validate(privacy).model_dump(),
        "profile_photo": profile_photo,
        "photo_count": len(photos),
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
    }
    return payload


@router.get("/me", summary="Get my full profile", response_model=ApiResponse[OwnProfileResponse])
async def get_my_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[OwnProfileResponse]:
    payload = await _own_payload(session, user)
    return ApiResponse(data=OwnProfileResponse(**payload))


@router.post("", summary="Create my profile", response_model=ApiResponse[OwnProfileResponse])
async def create_profile(
    body: ProfileCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[OwnProfileResponse]:
    service = ProfileService(session)
    await service.create(user, body.model_dump(exclude_unset=True))
    await session.commit()
    payload = await _own_payload(session, user)
    return ApiResponse(data=OwnProfileResponse(**payload))


@router.patch("", summary="Update my profile", response_model=ApiResponse[OwnProfileResponse])
async def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[OwnProfileResponse]:
    service = ProfileService(session)
    await service.update(user, body.model_dump(exclude_unset=True))
    await session.commit()
    payload = await _own_payload(session, user)
    return ApiResponse(data=OwnProfileResponse(**payload))


@router.delete("", summary="Delete my account (soft delete)", response_model=ApiResponse[dict])
async def delete_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = ProfileService(session)
    await service.delete_account(user)
    await session.commit()
    return ApiResponse(data={"status": "deleted"})


@router.get("/privacy", summary="Get privacy settings", response_model=ApiResponse[PrivacySettingsResponse])
async def get_privacy(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PrivacySettingsResponse]:
    settings = await UserRepository(session).get_privacy(user.id)
    return ApiResponse(data=PrivacySettingsResponse.model_validate(settings))


@router.patch("/privacy", summary="Update privacy settings", response_model=ApiResponse[PrivacySettingsResponse])
async def update_privacy(
    body: PrivacySettingsUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PrivacySettingsResponse]:
    repo = UserRepository(session)
    settings = await repo.get_privacy(user.id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await session.commit()
    return ApiResponse(data=PrivacySettingsResponse.model_validate(settings))
