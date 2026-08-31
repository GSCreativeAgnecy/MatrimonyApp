from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repo import AuditLogRepository

# Events that should always be logged
SENSITIVE_EVENTS = frozenset(
    {
        "auth.login",
        "auth.logout",
        "auth.password_change",
        "auth.password_reset",
        "auth.register",
        "profile.update",
        "profile.delete",
        "verification.review",
        "admin.ban",
        "admin.unban",
        "admin.role_change",
        "report.create",
        "subscription.change",
        "payment.event",
        "user.delete",
        "app_config.created",
        "app_config.updated",
        "app_config.deactivated",
    }
)


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditLogRepository(session)

    async def record(
        self,
        *,
        action: str,
        actor_user_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | UUID | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        await self.repo.create_log(
            action=action,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            meta=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )
