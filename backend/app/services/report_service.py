from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ForbiddenError, NotFoundError, ValidationAppError
from app.db.enums import ReportStatus
from app.db.models import Report, User
from app.repositories.moderation_repo import ReportRepository
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService

ALLOWED_STATUSES = {s.value for s in ReportStatus}


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ReportRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditService(session)

    async def create(
        self, reporter: User, reported_user_id: UUID, reason: str, description: str | None = None
    ) -> Report:
        if str(reporter.id) == str(reported_user_id):
            raise ForbiddenError("You cannot report yourself", code="SELF_REPORT")
        target = await self.users.get(reported_user_id)
        if not target:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        report = await self.repo.create(
            reporter_id=reporter.id,
            reported_user_id=reported_user_id,
            reason=reason,
            description=description,
            status=ReportStatus.PENDING.value,
        )
        await self.audit.record(
            action="report.create", actor_user_id=reporter.id, entity_type="report", entity_id=str(report.id)
        )
        return report

    # ---------- admin moderation ----------

    async def get_or_404(self, report_id: UUID) -> Report:
        report = await self.session.get(Report, report_id)
        if report is None:
            raise NotFoundError("Report not found", code="REPORT_NOT_FOUND")
        return report

    async def assign(self, moderator: User, report_id: UUID, *, assignee_id: UUID) -> Report:
        report = await self.get_or_404(report_id)
        assignee = await self.users.get(assignee_id)
        if assignee is None:
            raise NotFoundError("Assignee not found", code="USER_NOT_FOUND")
        report.reviewed_by = assignee.id
        if report.status == ReportStatus.PENDING.value:
            report.status = ReportStatus.UNDER_REVIEW.value
        report.reviewed_at = datetime.now(UTC)
        await self.audit.record(
            action="report.assign",
            actor_user_id=moderator.id,
            entity_type="report",
            entity_id=str(report.id),
            metadata={"assignee_id": str(assignee_id)},
        )
        return report

    async def transition(self, moderator: User, report_id: UUID, *, status: str, reason: str | None = None) -> Report:
        if status not in ALLOWED_STATUSES:
            raise ValidationAppError(f"Invalid report status: {status}", code="INVALID_REPORT_STATUS")
        report = await self.get_or_404(report_id)
        report.status = status
        report.reviewed_by = moderator.id
        report.reviewed_at = datetime.now(UTC)
        await self.audit.record(
            action="report.review",
            actor_user_id=moderator.id,
            entity_type="report",
            entity_id=str(report.id),
            metadata={"status": status, "reason": reason},
        )
        return report

    async def history(self, report_id: UUID) -> list[dict]:
        from app.db.models import AuditLog

        rows = (
            (
                await self.session.execute(
                    select(AuditLog)
                    .where(AuditLog.entity_type == "report", AuditLog.entity_id == str(report_id))
                    .order_by(AuditLog.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": str(a.id),
                "action": a.action,
                "actor_user_id": str(a.actor_user_id) if a.actor_user_id else None,
                "details": a.meta,
                "created_at": a.created_at,
            }
            for a in rows
        ]
