from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_context, get_session, require_permission
from app.db.enums import AccountStatus, UserRole
from app.db.models import User
from app.repositories.user_repo import RefreshTokenRepository, UserRepository
from app.schemas.admin import (
    AdminActionResponse,
    AdminUserCreate,
    AdminUserRow,
    RolePermissionsResponse,
    RolePermissionsUpdate,
)
from app.schemas.common import ApiResponse
from app.security.password import hash_password
from app.services.admin_user_service import AdminUserService
from app.services.audit_service import AuditService
from app.services.permission_service import PermissionService
from app.services.totp_service import TotpService

router = APIRouter(prefix="/admin", tags=["admin", "admin-users"])

can_read = require_permission("admin_users.read")
can_manage = require_permission("admin_users.manage")

ADMIN_ROLE_NAMES = {
    "MODERATOR",
    "VERIFIER",
    "SUPPORT",
    "FINANCE",
    "ANALYST",
    "ADMIN",
    "SUPER_ADMIN",
}


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("/admin-users", summary="List admin users", response_model=ApiResponse[list[AdminUserRow]])
async def list_admin_users(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    role: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[AdminUserRow]]:
    stmt = select(User).where(User.role.in_([r.value for r in UserRole if r.value in ADMIN_ROLE_NAMES]))
    count_stmt = (
        select(func.count())
        .select_from(User)
        .where(User.role.in_([r.value for r in UserRole if r.value in ADMIN_ROLE_NAMES]))
    )
    if role:
        stmt = stmt.where(User.role == role)
        count_stmt = count_stmt.where(User.role == role)
    total = int((await session.execute(count_stmt)).scalar_one())
    rows = list(
        (await session.execute(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    )
    totp = TotpService(session)
    return ApiResponse(
        data=[
            AdminUserRow(
                id=str(u.id),
                email=u.email,
                name=(u.email or "").split("@")[0],
                role=u.role.value,
                account_status=u.account_status.value,
                is_banned=u.is_banned,
                two_factor_enabled=await totp.is_enabled(u.id),
                last_login_at=u.last_login_at,
                created_at=u.created_at,
            )
            for u in rows
        ],
        meta=_meta(total, limit, offset),
    )


@router.post("/admin-users", summary="Create or promote an admin", response_model=ApiResponse[AdminUserRow])
async def create_admin(
    payload: AdminUserCreate,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminUserRow]:
    ctx = await get_request_context(request)
    repo = UserRepository(session)
    user = await repo.get_by_email(payload.email)
    if user is None:
        if not payload.password:
            from app.api.errors import ValidationAppError

            raise ValidationAppError("A password is required for a new account", code="PASSWORD_REQUIRED")
        user = await repo.create(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            account_status=AccountStatus.ACTIVE,
            role=UserRole(payload.role),
        )
        await session.flush()
    else:
        new_role = UserRole(payload.role)
        if user.role == UserRole.SUPER_ADMIN and admin.role != UserRole.SUPER_ADMIN:
            from app.api.errors import ForbiddenError

            raise ForbiddenError("Only a SUPER_ADMIN can manage a SUPER_ADMIN", code="FORBIDDEN")
        if new_role == UserRole.SUPER_ADMIN and admin.role != UserRole.SUPER_ADMIN:
            from app.api.errors import ForbiddenError

            raise ForbiddenError("Only a SUPER_ADMIN can grant SUPER_ADMIN", code="FORBIDDEN")
        user.role = new_role
    await AuditService(session).record(
        action="admin.admin_created",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=str(user.id),
        metadata={"email": payload.email, "role": payload.role},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(
        data=AdminUserRow(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
            account_status=user.account_status.value,
            two_factor_enabled=await TotpService(session).is_enabled(user.id),
            created_at=user.created_at,
        )
    )


@router.patch(
    "/admin-users/{user_id}/role", summary="Change an admin's role", response_model=ApiResponse[AdminActionResponse]
)
async def change_admin_role(
    user_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    new_role = payload.get("role")
    if new_role not in ADMIN_ROLE_NAMES:
        from app.api.errors import ValidationAppError

        raise ValidationAppError("Invalid admin role", code="INVALID_ROLE")
    await AdminUserService(session).change_role(
        admin, user_id, UserRole(new_role), ip_address=ctx["ip"], user_agent=ctx["user_agent"]
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="updated", message="Role updated"))


@router.post(
    "/admin-users/{user_id}/disable", summary="Disable an admin", response_model=ApiResponse[AdminActionResponse]
)
async def disable_admin(
    user_id: UUID,
    payload: dict,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    service = AdminUserService(session)
    target = await service.get_user(user_id)
    if target.id == admin.id:
        from app.api.errors import ForbiddenError

        raise ForbiddenError("You cannot disable your own account", code="FORBIDDEN")
    if target.role == UserRole.SUPER_ADMIN and admin.role != UserRole.SUPER_ADMIN:
        from app.api.errors import ForbiddenError

        raise ForbiddenError("Only a SUPER_ADMIN can disable a SUPER_ADMIN", code="FORBIDDEN")
    target.account_status = AccountStatus.SUSPENDED
    target.suspended_reason = payload.get("reason", "Admin account disabled")
    target.suspended_by = admin.id
    await RefreshTokenRepository(session).revoke_all_for_user(target.id)
    await AuditService(session).record(
        action="admin.admin_disabled",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=str(user_id),
        metadata={"reason": payload.get("reason")},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="disabled", message="Admin disabled"))


@router.post(
    "/admin-users/{user_id}/enable", summary="Re-enable an admin", response_model=ApiResponse[AdminActionResponse]
)
async def enable_admin(
    user_id: UUID,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    target = await AdminUserService(session).get_user(user_id)
    target.account_status = AccountStatus.ACTIVE
    target.suspended_until = None
    await AuditService(session).record(
        action="admin.admin_enabled",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=str(user_id),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="enabled", message="Admin enabled"))


@router.post(
    "/admin-users/{user_id}/reset-2fa",
    summary="Reset an admin's two-factor",
    response_model=ApiResponse[AdminActionResponse],
)
async def reset_admin_2fa(
    user_id: UUID,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await AdminUserService(session).reset_2fa(admin, user_id)
    await AuditService(session).record(
        action="admin.totp_reset",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=str(user_id),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="reset", message="Two-factor reset"))


@router.post(
    "/admin-users/{user_id}/revoke-sessions",
    summary="Revoke all sessions",
    response_model=ApiResponse[AdminActionResponse],
)
async def revoke_sessions(
    user_id: UUID,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    await AdminUserService(session).revoke_sessions(admin, user_id)
    await AuditService(session).record(
        action="admin.revoke_sessions",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=str(user_id),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="revoked", message="Sessions revoked"))


# ---------- roles & permissions ----------


@router.get(
    "/roles", summary="List roles and their permissions", response_model=ApiResponse[list[RolePermissionsResponse]]
)
async def list_roles(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[RolePermissionsResponse]]:
    data = await PermissionService(session).all_roles()
    return ApiResponse(data=[RolePermissionsResponse(role=r, permissions=p) for r, p in data.items()])


@router.put(
    "/roles/{role}/permissions",
    summary="Set a role's permissions",
    response_model=ApiResponse[RolePermissionsResponse],
)
async def set_role_permissions(
    role: str,
    payload: RolePermissionsUpdate,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[RolePermissionsResponse]:
    ctx = await get_request_context(request)
    if role not in ADMIN_ROLE_NAMES:
        from app.api.errors import ValidationAppError

        raise ValidationAppError("Invalid role", code="INVALID_ROLE")
    permissions = await PermissionService(session).set_permissions_for_role(admin, UserRole(role), payload.permissions)
    await AuditService(session).record(
        action="admin.role_permissions_update",
        actor_user_id=admin.id,
        entity_type="role_permission",
        entity_id=role,
        metadata={"permissions": permissions},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=RolePermissionsResponse(role=role, permissions=permissions))
