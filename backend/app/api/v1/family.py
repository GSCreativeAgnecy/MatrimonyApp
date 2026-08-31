from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.family_astrology import (
    AstrologyResponse,
    AstrologyUpdate,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    FamilyResponse,
    FamilyUpdate,
)
from app.services.astrology_service import AstrologyService
from app.services.family_service import FamilyService

router = APIRouter(tags=["family", "astrology"])


# ---------- family ----------


@router.get("/family", summary="Get my family details", response_model=ApiResponse[FamilyResponse])
async def get_family(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[FamilyResponse]:
    service = FamilyService(session)
    family = await service.get_family(user.id)
    await session.commit()
    return ApiResponse(data=FamilyResponse.model_validate(family))


@router.put("/family", summary="Update family details", response_model=ApiResponse[FamilyResponse])
async def update_family(
    body: FamilyUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[FamilyResponse]:
    service = FamilyService(session)
    family = await service.update_family(user.id, body.model_dump(exclude_unset=True))
    await session.commit()
    return ApiResponse(data=FamilyResponse.model_validate(family))


@router.get("/family/members", summary="List family members", response_model=ApiResponse[list[FamilyMemberResponse]])
async def list_members(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[FamilyMemberResponse]]:
    service = FamilyService(session)
    members = await service.list_members(user.id)
    return ApiResponse(data=[FamilyMemberResponse.model_validate(m) for m in members])


@router.post("/family/members", summary="Add a family member", response_model=ApiResponse[FamilyMemberResponse])
async def add_member(
    body: FamilyMemberCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[FamilyMemberResponse]:
    service = FamilyService(session)
    member = await service.add_member(user.id, body.model_dump())
    await session.commit()
    return ApiResponse(data=FamilyMemberResponse.model_validate(member))


@router.patch(
    "/family/members/{member_id}", summary="Update a family member", response_model=ApiResponse[FamilyMemberResponse]
)
async def update_member(
    member_id: UUID,
    body: FamilyMemberUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[FamilyMemberResponse]:
    service = FamilyService(session)
    member = await service.update_member(user.id, member_id, body.model_dump(exclude_unset=True))
    await session.commit()
    return ApiResponse(data=FamilyMemberResponse.model_validate(member))


@router.delete("/family/members/{member_id}", summary="Delete a family member", response_model=ApiResponse[dict])
async def delete_member(
    member_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = FamilyService(session)
    await service.delete_member(user.id, member_id)
    await session.commit()
    return ApiResponse(data={"status": "deleted"})


# ---------- astrology ----------


@router.get("/astrology", summary="Get my astrology profile", response_model=ApiResponse[AstrologyResponse])
async def get_astrology(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AstrologyResponse]:
    service = AstrologyService(session)
    profile = await service.get(user.id)
    await session.commit()
    return ApiResponse(data=AstrologyResponse.model_validate(profile))


@router.put("/astrology", summary="Update my astrology profile", response_model=ApiResponse[AstrologyResponse])
async def update_astrology(
    body: AstrologyUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AstrologyResponse]:
    service = AstrologyService(session)
    profile = await service.update(user.id, body.model_dump(exclude_unset=True))
    await session.commit()
    return ApiResponse(data=AstrologyResponse.model_validate(profile))


@router.post(
    "/astrology/calculate", summary="Calculate horoscope via provider", response_model=ApiResponse[AstrologyResponse]
)
async def calculate_astrology(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AstrologyResponse]:
    service = AstrologyService(session)
    profile = await service.calculate_chart(user.id)
    await session.commit()
    return ApiResponse(data=AstrologyResponse.model_validate(profile))
