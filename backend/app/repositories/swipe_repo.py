from uuid import UUID

from sqlalchemy import select

from app.db.enums import SwipeAction
from app.db.models import Swipe
from app.repositories.base import BaseRepository


class SwipeRepository(BaseRepository[Swipe]):
    model = Swipe

    async def get_recent(self, from_user_id: UUID, to_user_id: UUID) -> Swipe | None:
        stmt = (
            select(Swipe)
            .where(Swipe.from_user_id == from_user_id, Swipe.to_user_id == to_user_id)
            .order_by(Swipe.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def liked_by(self, user_id: UUID, candidate_id: UUID) -> Swipe | None:
        stmt = (
            select(Swipe)
            .where(
                Swipe.from_user_id == user_id,
                Swipe.to_user_id == candidate_id,
                Swipe.action.in_([SwipeAction.LIKE, SwipeAction.SUPER_LIKE]),
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def swiped_user_ids(self, user_id: UUID) -> list[UUID]:
        stmt = select(Swipe.to_user_id).where(Swipe.from_user_id == user_id)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [UUID(str(r)) for r in rows]

    async def mutual_like_exists(self, a: UUID, b: UUID) -> bool:
        stmt = (
            select(Swipe.id)
            .where(
                Swipe.from_user_id == a,
                Swipe.to_user_id == b,
                Swipe.action.in_([SwipeAction.LIKE, SwipeAction.SUPER_LIKE]),
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None
