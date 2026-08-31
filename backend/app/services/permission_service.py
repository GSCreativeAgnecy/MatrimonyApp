from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import UserRole
from app.db.models import RolePermission
from app.security.permissions import (
    ALL_PERMISSIONS,
    permissions_for_role_default,
)
from app.services.audit_service import AuditService


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def permissions_for_role(self, role: UserRole) -> set[str]:
        """Effective permissions for a role.

        Prefers the ``role_permissions`` table (runtime-overridable); falls back
        to the static registry when the table has no rows for the role, so a
        fresh database still enforces sane defaults without a seed.
        """
        rows = (
            (await self.session.execute(select(RolePermission.permission).where(RolePermission.role == role.value)))
            .scalars()
            .all()
        )
        if rows:
            return set(rows)
        return permissions_for_role_default(role)

    async def all_roles(self) -> dict[str, list[str]]:
        """Role -> permissions map for every admin-visible role."""
        result: dict[str, list[str]] = {}
        for role in UserRole:
            if role == UserRole.USER:
                continue
            result[role.value] = sorted(await self.permissions_for_role(role))
        return result

    async def set_permissions_for_role(self, actor: object, role: UserRole, permissions: list[str]) -> list[str]:
        invalid = set(permissions) - set(ALL_PERMISSIONS)
        if invalid:
            from app.api.errors import ValidationAppError

            raise ValidationAppError(f"Unknown permission(s): {sorted(invalid)}", code="INVALID_PERMISSION")

        # SUPER_ADMIN cannot be stripped of anything (invariant).
        if role == UserRole.SUPER_ADMIN:
            permissions = sorted(ALL_PERMISSIONS)

        await self.session.execute(delete(RolePermission).where(RolePermission.role == role.value))
        for permission in sorted(set(permissions)):
            self.session.add(RolePermission(role=role.value, permission=permission))
        await self.session.flush()
        await self.audit.record(
            action="admin.role_permissions_update",
            actor_user_id=getattr(actor, "id", None),
            entity_type="role_permission",
            entity_id=role.value,
            metadata={"permissions": sorted(set(permissions))},
        )
        return sorted(set(permissions))

    async def has_permission(self, user: object, permission: str) -> bool:
        role = getattr(user, "role", None)
        if role is None:
            return False
        return permission in await self.permissions_for_role(role)
