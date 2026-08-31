from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select

from app.db.models import Block, Report, User
from app.repositories.base import BaseRepository


class BlockRepository(BaseRepository[Block]):
    model = Block

    async def get_pair(self, blocker_id: UUID, blocked_id: UUID) -> Block | None:
        return await self.session.scalar(
            select(Block).where(Block.blocker_id == blocker_id, Block.blocked_id == blocked_id)
        )

    async def blocked_ids(self, user_id: UUID) -> list[UUID]:
        stmt = select(Block.blocked_id).where(Block.blocker_id == user_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def who_blocked_me(self, user_id: UUID) -> list[UUID]:
        stmt = select(Block.blocker_id).where(Block.blocked_id == user_id)
        return list((await self.session.execute(stmt)).scalars().all())


class ReportRepository(BaseRepository[Report]):
    model = Report

    async def list_by_status(self, status: str | None = None, *, limit: int = 50, offset: int = 0) -> list[Report]:
        stmt = select(Report)
        if status:
            stmt = stmt.where(Report.status == status)
        stmt = stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def admin_list(
        self,
        *,
        statuses: list[str] | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[tuple[Report, str | None, str | None]], int]:
        reporter = User.__table__.alias("reporter")
        reported = User.__table__.alias("reported")
        stmt = (
            select(Report, reporter.c.email.label("reporter_email"), reported.c.email.label("reported_email"))
            .outerjoin(reporter, reporter.c.id == Report.reporter_id)
            .outerjoin(reported, reported.c.id == Report.reported_user_id)
        )
        count_stmt = select(func.count()).select_from(Report)
        conds: list[Any] = []
        if statuses:
            conds.append(Report.status.in_(statuses))
        if search:
            like = f"%{search}%"
            conds.append(
                or_(
                    reporter.c.email.ilike(like),
                    reported.c.email.ilike(like),
                    Report.reason.ilike(like),
                    Report.description.ilike(like),
                )
            )
        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (await self.session.execute(stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset))).all()
        return [(row[0], row[1], row[2]) for row in rows], total

    async def detail(self, report_id: UUID) -> tuple[Report | None, User | None, User | None]:
        from sqlalchemy.orm import aliased

        reporter = aliased(User)
        reported = aliased(User)
        stmt = (
            select(Report, reporter, reported)
            .outerjoin(reporter, reporter.id == Report.reporter_id)
            .outerjoin(reported, reported.id == Report.reported_user_id)
            .where(Report.id == report_id)
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            return None, None, None
        return row[0], row[1], row[2]
