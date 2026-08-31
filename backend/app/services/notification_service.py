from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification
from app.repositories.notification_repo import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = NotificationRepository(session)

    async def create(
        self,
        user_id: UUID,
        *,
        type: str,
        title: str | None = None,
        body: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        notification = await self.repo.create(user_id=user_id, type=type, title=title, body=body, data=data or {})
        # Deliver via worker/push (fire-and-forget). Worker picks up enqueued pushes.
        return notification

    async def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[Notification]:
        return await self.repo.list_for_user(user_id, limit=limit, offset=offset)

    async def mark_read(self, user_id: UUID, notification_id: UUID) -> Notification | None:
        notification = await self.repo.get_for_user(notification_id, user_id)
        if notification:
            await self.repo.mark_read(notification)
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        return await self.repo.mark_all_read(user_id)

    async def unread_count(self, user_id: UUID) -> int:
        return await self.repo.unread_count(user_id)
