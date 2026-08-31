from uuid import UUID

from app.db.models import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def create_log(
        self,
        *,
        action: str,
        actor_user_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        meta: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        return await self.create(
            action=action,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=meta,
            ip_address=ip_address,
            user_agent=user_agent,
        )
