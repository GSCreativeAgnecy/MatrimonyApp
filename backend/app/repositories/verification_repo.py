from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select

from app.db.enums import JobVerificationStatus
from app.db.models import JobVerification, User
from app.repositories.base import BaseRepository


class VerificationRepository(BaseRepository[JobVerification]):
    model = JobVerification

    async def latest_for_user(self, user_id: UUID) -> JobVerification | None:
        stmt = (
            select(JobVerification)
            .where(JobVerification.user_id == user_id)
            .order_by(JobVerification.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def get_for_user(self, verification_id: UUID, user_id: UUID) -> JobVerification | None:
        return await self.session.scalar(
            select(JobVerification).where(JobVerification.id == verification_id, JobVerification.user_id == user_id)
        )

    async def list_by_status(self, status: JobVerificationStatus | None = None) -> list[JobVerification]:
        stmt = select(JobVerification).order_by(JobVerification.created_at.desc())
        if status:
            stmt = stmt.where(JobVerification.verification_status == status)
        return list((await self.session.execute(stmt)).scalars().all())

    async def admin_list(
        self,
        *,
        statuses: list[str] | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        stmt = select(JobVerification, User.email).outerjoin(User, User.id == JobVerification.user_id)
        count_stmt = select(func.count()).select_from(JobVerification)
        conds: list[Any] = []
        if statuses:
            conds.append(JobVerification.verification_status.in_(statuses))
        if search:
            like = f"%{search}%"
            conds.append(
                or_(
                    User.email.ilike(like),
                    User.phone_number.ilike(like),
                    JobVerification.employer_name.ilike(like),
                    JobVerification.job_title.ilike(like),
                )
            )
        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (
            await self.session.execute(stmt.order_by(JobVerification.created_at.desc()).limit(limit).offset(offset))
        ).all()
        return (
            [
                {
                    "id": str(v.id),
                    "user_id": str(v.user_id),
                    "user_name": user_email,
                    "employment_type": v.employment_type.value,
                    "employer_name": v.employer_name,
                    "job_title": v.job_title,
                    "country": v.country,
                    "verification_status": v.verification_status.value,
                    "amount_paid": v.amount_paid,
                    "currency": v.currency,
                    "submitted_at": v.submitted_at,
                    "verified_at": v.verified_at,
                    "expires_at": v.expires_at,
                    "reviewer_notes": v.reviewer_notes,
                    "rejection_reason": v.rejection_reason,
                    "created_at": v.created_at,
                }
                for v, user_email in rows
            ],
            total,
        )
