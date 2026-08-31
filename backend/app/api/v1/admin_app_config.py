from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_role
from app.api.errors import ValidationAppError
from app.db.enums import ConfigCategory
from app.db.models import User
from app.schemas.app_config import AppConfigAdminResponse, AppConfigCreate, AppConfigUpdate
from app.schemas.common import ApiResponse
from app.services.app_config_service import AppConfigService, admin_response

router = APIRouter(prefix="/admin/app-config", tags=["admin", "app-config"])

admin_only = require_role("ADMIN", "SUPER_ADMIN")


def _parse_category(category: str | None) -> ConfigCategory | None:
    if category is None:
        return None
    try:
        return ConfigCategory(category)
    except ValueError as exc:
        raise ValidationAppError(
            f"Invalid category. Allowed: {[c.value for c in ConfigCategory]}",
            code="INVALID_CONFIG_CATEGORY",
        ) from exc


@router.get("", summary="List configuration entries (admin)", response_model=ApiResponse[list[AppConfigAdminResponse]])
async def list_config(
    admin: User = Depends(admin_only),
    session: AsyncSession = Depends(get_session),
    category: str | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[AppConfigAdminResponse]]:
    service = AppConfigService(session)
    rows = await service.list_admin(
        category=_parse_category(category),
        is_public=is_public,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        data=[admin_response(r) for r in rows],
        meta={"limit": limit, "offset": offset, "count": len(rows)},
    )


@router.get(
    "/{key}", summary="Get one configuration entry (admin)", response_model=ApiResponse[AppConfigAdminResponse]
)
async def get_config(
    key: str,
    admin: User = Depends(admin_only),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AppConfigAdminResponse]:
    service = AppConfigService(session)
    obj = await service.get_by_key(key)
    return ApiResponse(data=admin_response(obj))


@router.post("", summary="Create a configuration entry (admin)", response_model=ApiResponse[AppConfigAdminResponse])
async def create_config(
    body: AppConfigCreate,
    admin: User = Depends(admin_only),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AppConfigAdminResponse]:
    service = AppConfigService(session)
    obj = await service.create(admin, body.model_dump())
    await session.commit()
    return ApiResponse(data=admin_response(obj))


@router.patch(
    "/{key}", summary="Update a configuration entry (admin)", response_model=ApiResponse[AppConfigAdminResponse]
)
async def update_config(
    key: str,
    body: AppConfigUpdate,
    admin: User = Depends(admin_only),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AppConfigAdminResponse]:
    service = AppConfigService(session)
    obj = await service.update(admin, key, body.model_dump(exclude_unset=True))
    await session.commit()
    return ApiResponse(data=admin_response(obj))


@router.delete(
    "/{key}",
    summary="Deactivate a configuration entry (admin)",
    description="Soft deactivation: sets ``is_active=false`` instead of deleting the row.",
    response_model=ApiResponse[dict],
)
async def deactivate_config(
    key: str,
    admin: User = Depends(admin_only),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = AppConfigService(session)
    await service.deactivate(admin, key)
    await session.commit()
    return ApiResponse(data={"status": "deactivated", "key": key})
