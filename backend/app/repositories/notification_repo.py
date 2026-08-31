from datetime import UTC
from uuid import UUID

from sqlalchemy import select

from app.db.models import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    async def list_for_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_for_user(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        return await self.session.scalar(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
        )

    async def mark_read(self, notification: Notification) -> None:
        from datetime import datetime

        notification.is_read = True
        notification.read_at = datetime.now(UTC)

    async def mark_all_read(self, user_id: UUID) -> int:
        from datetime import datetime

        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        rows = (await self.session.execute(stmt)).scalars().all()
        now = datetime.now(UTC)
        for n in rows:
            n.is_read = True
            n.read_at = now
        return len(rows)

    async def unread_count(self, user_id: UUID) -> int:
        stmt = select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        rows = (await self.session.execute(stmt)).scalars().all()
        return len(rows)
