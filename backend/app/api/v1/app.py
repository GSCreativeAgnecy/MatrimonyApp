from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.app_config import PublicAppConfigResponse
from app.schemas.common import ApiResponse
from app.services.app_config_service import AppConfigService

router = APIRouter(prefix="/app", tags=["app"])


@router.get(
    "/config",
    summary="Get public app configuration (branding, features, limits, versions, ...)",
    description=(
        "Public, unauthenticated endpoint. Returns only entries with "
        "``is_public=true`` and ``is_active=true``, grouped by category, plus a "
        "content-derived ``meta.version`` the mobile app can use to detect stale "
        "local caches. Always available, including during maintenance."
    ),
    response_model=ApiResponse[PublicAppConfigResponse],
)
async def get_public_config(
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[PublicAppConfigResponse]:
    service = AppConfigService(session)
    grouped, version = await service.get_public()
    return ApiResponse(data=PublicAppConfigResponse(**grouped), meta={"version": version})
