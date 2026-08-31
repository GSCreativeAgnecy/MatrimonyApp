from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select

from app.db.enums import MatchStatus
from app.db.models import Match, User
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    model = Match

    @staticmethod
    def normalize(a: UUID, b: UUID) -> tuple[UUID, UUID]:
        def _as_uuid(x: UUID) -> UUID:
            return UUID(str(x)) if not isinstance(x, UUID) else x

        a, b = _as_uuid(a), _as_uuid(b)
        return (min(a, b), max(a, b))

    async def get_between(self, a: UUID, b: UUID) -> Match | None:
        u1, u2 = self.normalize(a, b)
        return await self.session.scalar(select(Match).where(Match.user1_id == u1, Match.user2_id == u2))

    async def get_active_between(self, a: UUID, b: UUID) -> Match | None:
        m = await self.get_between(a, b)
        return m if m and m.status == MatchStatus.ACTIVE else None

    async def active_match_ids_for(self, user_id: UUID) -> list[UUID]:
        stmt = select(Match.id).where(
            or_(Match.user1_id == user_id, Match.user2_id == user_id),
            Match.status == MatchStatus.ACTIVE,
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def matches_for(self, user_id: UUID) -> list[Match]:
        stmt = (
            select(Match)
            .where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id),
                Match.status == MatchStatus.ACTIVE,
            )
            .order_by(Match.matched_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    def other_user_id(self, match: Match, me: UUID) -> UUID:
        return match.user2_id if match.user1_id == me else match.user1_id

    async def create_between(self, a: UUID, b: UUID) -> Match:
        u1, u2 = self.normalize(a, b)
        return await self.create(user1_id=u1, user2_id=u2, status=MatchStatus.ACTIVE)

    # ---------- admin ----------

    async def admin_search(
        self,
        *,
        user_id: UUID | None = None,
        search: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        u1 = User.__table__.alias("u1")
        u2 = User.__table__.alias("u2")
        stmt = (
            select(
                Match,
                u1.c.email.label("user1_email"),
                u2.c.email.label("user2_email"),
            )
            .outerjoin(u1, u1.c.id == Match.user1_id)
            .outerjoin(u2, u2.c.id == Match.user2_id)
        )
        count_stmt = select(func.count()).select_from(Match)
        conds = []
        if user_id is not None:
            conds.append(or_(Match.user1_id == user_id, Match.user2_id == user_id))
        if search:
            like = f"%{search}%"
            conds.append(or_(u1.c.email.ilike(like), u2.c.email.ilike(like)))
        if status:
            conds.append(Match.status == status)
        if date_from is not None:
            conds.append(Match.matched_at >= date_from)
        if date_to is not None:
            conds.append(Match.matched_at < date_to)
        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (await self.session.execute(stmt.order_by(Match.matched_at.desc()).limit(limit).offset(offset))).all()
        return (
            [
                {
                    "id": str(m.id),
                    "user1_id": str(m.user1_id),
                    "user2_id": str(m.user2_id),
                    "user1_name": user1_email,
                    "user2_name": user2_email,
                    "status": m.status.value,
                    "matched_at": m.matched_at,
                    "unmatched_at": m.unmatched_at,
                    "created_at": m.created_at,
                }
                for m, user1_email, user2_email in rows
            ],
            total,
        )
