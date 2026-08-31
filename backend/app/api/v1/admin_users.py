from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_context, get_session, require_permission
from app.db.enums import UserRole
from app.db.models import User
from app.schemas.admin import (
    AdminActionResponse,
    AdminUserDetail,
    AdminUserListRow,
    BanRequest,
    DeleteUserRequest,
    RoleChangeRequest,
    SuspendRequest,
    VerifyUserRequest,
)
from app.schemas.common import ApiResponse
from app.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/admin/users", tags=["admin", "users"])

can_read = require_permission("users.read")
can_suspend = require_permission("users.suspend")
can_ban = require_permission("users.ban")
can_delete = require_permission("users.delete")
can_update = require_permission("users.update")
can_manage_admins = require_permission("admin_users.manage")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("", summary="List users (admin)", response_model=ApiResponse[list[AdminUserListRow]])
async def list_users(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    search: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    age_min: int | None = Query(default=None, ge=18, le=100),
    age_max: int | None = Query(default=None, ge=18, le=100),
    city: str | None = Query(default=None),
    state: str | None = Query(default=None),
    country: str | None = Query(default=None),
    religion: str | None = Query(default=None),
    caste: str | None = Query(default=None),
    education: str | None = Query(default=None),
    occupation: str | None = Query(default=None),
    premium: bool | None = Query(default=None),
    verified: bool | None = Query(default=None),
    account_status: str | None = Query(default=None),
    registered_from: datetime | None = Query(default=None),
    registered_to: datetime | None = Query(default=None),
    active_from: datetime | None = Query(default=None),
    active_to: datetime | None = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[AdminUserListRow]]:
    statuses = account_status.split(",") if account_status else None
    rows, total = await AdminUserService(session).users.admin_search(
        search=search,
        gender=gender,
        age_min=age_min,
        age_max=age_max,
        city=city,
        state=state,
        country=country,
        religion=religion,
        caste=caste,
        education=education,
        occupation=occupation,
        premium=premium,
        verified=verified,
        account_status=statuses,
        registered_from=registered_from,
        registered_to=registered_to,
        active_from=active_from,
        active_to=active_to,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[AdminUserListRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.get("/{user_id}", summary="User detail (admin)", response_model=ApiResponse[AdminUserDetail])
async def user_detail(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminUserDetail]:
    data = await AdminUserService(session).detail(user_id)
    return ApiResponse(data=AdminUserDetail(**data))


@router.get("/{user_id}/profile", summary="Full profile review payload", response_model=ApiResponse[dict])
async def user_profile(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    return ApiResponse(data=await AdminUserService(session).profile(user_id))


@router.get("/{user_id}/photos", summary="User photos", response_model=ApiResponse[list[dict]])
async def user_photos(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).photos(user_id))


@router.get("/{user_id}/verifications", summary="User verifications", response_model=ApiResponse[list[dict]])
async def user_verifications(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).verifications(user_id))


@router.get("/{user_id}/matches", summary="User matches", response_model=ApiResponse[list[dict]])
async def user_matches(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).matches(user_id))


@router.get(
    "/{user_id}/conversations", summary="User conversations (metadata only)", response_model=ApiResponse[list[dict]]
)
async def user_conversations(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).conversations(user_id))


@router.get("/{user_id}/payments", summary="User payments", response_model=ApiResponse[list[dict]])
async def user_payments(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).payments(user_id))


@router.get("/{user_id}/reports", summary="User reports", response_model=ApiResponse[list[dict]])
async def user_reports(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).reports(user_id))


@router.get("/{user_id}/audit", summary="Audit trail involving this user", response_model=ApiResponse[list[dict]])
async def user_audit(
    user_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
) -> ApiResponse[list[dict]]:
    return ApiResponse(data=await AdminUserService(session).audit_trail(user_id, limit=limit))


# ---------- actions ----------


async def _ctx(request: Request) -> dict:
    return await get_request_context(request)


@router.post("/{user_id}/suspend", summary="Suspend a user", response_model=ApiResponse[AdminActionResponse])
async def suspend_user(
    user_id: UUID,
    payload: SuspendRequest,
    request: Request,
    admin: User = Depends(can_suspend),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).suspend(
        admin,
        user_id,
        reason=payload.reason,
        duration_minutes=payload.duration_minutes,
        notes=payload.admin_notes,
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="suspended", message="User suspended"))


@router.post("/{user_id}/ban", summary="Ban a user", response_model=ApiResponse[AdminActionResponse])
async def ban_user(
    user_id: UUID,
    payload: BanRequest,
    request: Request,
    admin: User = Depends(can_ban),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).ban(
        admin,
        user_id,
        reason=payload.reason,
        notes=payload.admin_notes,
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="banned", message="User banned"))


@router.post("/{user_id}/unban", summary="Unban a user", response_model=ApiResponse[AdminActionResponse])
async def unban_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(can_ban),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).unban(admin, user_id, ip_address=ctx["ip"], user_agent=ctx["user_agent"])
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="unbanned", message="User unbanned"))


@router.post("/{user_id}/delete", summary="Delete a user (soft)", response_model=ApiResponse[AdminActionResponse])
async def delete_user(
    user_id: UUID,
    payload: DeleteUserRequest,
    request: Request,
    admin: User = Depends(can_delete),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).delete_user(
        admin,
        user_id,
        reason=payload.reason,
        notes=payload.admin_notes,
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="deleted", message="User deleted"))


@router.post("/{user_id}/restore", summary="Restore a deleted user", response_model=ApiResponse[AdminActionResponse])
async def restore_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(can_delete),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).restore(admin, user_id, ip_address=ctx["ip"], user_agent=ctx["user_agent"])
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="restored", message="User restored"))


@router.post(
    "/{user_id}/verify", summary="Verify email/phone for a user", response_model=ApiResponse[AdminActionResponse]
)
async def verify_user(
    user_id: UUID,
    payload: VerifyUserRequest,
    request: Request,
    admin: User = Depends(can_update),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).verify(
        admin, user_id, kind=payload.kind, ip_address=ctx["ip"], user_agent=ctx["user_agent"]
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="verified", message="Verification updated"))


@router.post("/{user_id}/role", summary="Change a user's role", response_model=ApiResponse[AdminActionResponse])
async def change_role(
    user_id: UUID,
    payload: RoleChangeRequest,
    request: Request,
    admin: User = Depends(can_manage_admins),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await _ctx(request)
    await AdminUserService(session).change_role(
        admin, user_id, UserRole(payload.role), ip_address=ctx["ip"], user_agent=ctx["user_agent"]
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="updated", message="Role updated"))
