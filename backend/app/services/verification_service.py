from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ForbiddenError, NotFoundError
from app.config.settings import settings
from app.db.enums import EmploymentType, JobVerificationStatus, PaymentType
from app.db.models import AppConfig, JobVerification, Payment, User
from app.repositories.verification_repo import VerificationRepository
from app.services.app_config_keys import PRICING_LOCAL_JOB_VERIFICATION, PRICING_NRI_JOB_VERIFICATION
from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService


class VerificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = VerificationRepository(session)
        self.audit = AuditService(session)

    async def _price_for(self, employment_type: EmploymentType) -> Decimal:
        current_key = {
            EmploymentType.LOCAL: PRICING_LOCAL_JOB_VERIFICATION,
            EmploymentType.NRI: PRICING_NRI_JOB_VERIFICATION,
        }[employment_type]
        legacy_key = {
            EmploymentType.LOCAL: "LOCAL_JOB_VERIFICATION_PRICE",
            EmploymentType.NRI: "NRI_JOB_VERIFICATION_PRICE",
        }[employment_type]

        row = await self.session.scalar(select(AppConfig).where(AppConfig.key == current_key))
        if row and row.value is not None and isinstance(row.value, (int, float)):
            return Decimal(str(row.value))

        # Backward compatibility with legacy JSON-format pricing rows.
        legacy = await self.session.scalar(select(AppConfig).where(AppConfig.key == legacy_key))
        if legacy and legacy.value and "amount" in legacy.value:
            return Decimal(str(legacy.value["amount"]))

        return Decimal(str(getattr(settings, legacy_key)))

    async def submit(self, user: User, data: dict) -> dict:
        employment_type = EmploymentType(data["employment_type"])
        price = await self._price_for(employment_type)
        verification = await self.repo.create(
            user_id=user.id,
            employment_type=employment_type.value,
            employer_name=data["employer_name"],
            job_title=data.get("job_title"),
            country=data.get("country"),
            verification_status=JobVerificationStatus.PENDING_PAYMENT,
        )
        await self.session.flush()

        payments = PaymentService(self.session)
        checkout = await payments.create_checkout(
            user,
            payment_type=PaymentType.JOB_VERIFICATION,
            amount=price,
            currency=settings.JOB_VERIFICATION_CURRENCY,
            metadata={
                "verification_id": str(verification.id),
                "description": f"Job verification ({employment_type.value})",
            },
        )
        verification.payment_id = UUID(checkout["payment_id"])
        verification.amount_paid = float(price)
        verification.currency = settings.JOB_VERIFICATION_CURRENCY
        verification.submitted_at = datetime.now(UTC)
        await self.session.flush()

        await self.audit.record(
            action="verification.submit",
            actor_user_id=user.id,
            entity_type="job_verification",
            entity_id=str(verification.id),
        )
        return {
            "verification_id": str(verification.id),
            "checkout_url": checkout["checkout_url"],
            "payment_id": checkout["payment_id"],
            "amount": float(price),
            "currency": settings.JOB_VERIFICATION_CURRENCY,
        }

    async def list_mine(self, user_id: UUID) -> list[JobVerification]:

        stmt = (
            select(JobVerification)
            .where(JobVerification.user_id == user_id)
            .order_by(JobVerification.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def mark_under_review_from_payment(self, payment: Payment) -> None:
        meta = payment.meta or {}
        verification_id = meta.get("verification_id")
        if not verification_id:
            raise NotFoundError("Missing verification metadata on payment", code="PAYMENT_META_MISSING")
        verification = await self.session.get(JobVerification, UUID(verification_id))
        if verification is None:
            raise NotFoundError("Verification not found", code="VERIFICATION_NOT_FOUND")
        if verification.verification_status == JobVerificationStatus.PENDING_PAYMENT:
            verification.verification_status = JobVerificationStatus.UNDER_REVIEW

    # ---------- admin / verifier ----------

    async def review(
        self,
        reviewer: User,
        verification_id: UUID,
        *,
        approve: bool,
        rejection_reason: str | None = None,
        reviewer_notes: str | None = None,
        expires_in_days: int = 365,
    ) -> JobVerification:
        if reviewer.role not in {"VERIFIER", "ADMIN", "SUPER_ADMIN"}:
            raise ForbiddenError("Not authorized to review verifications", code="FORBIDDEN")
        verification = await self.session.get(JobVerification, verification_id)
        if verification is None:
            raise NotFoundError("Verification not found", code="VERIFICATION_NOT_FOUND")

        if approve:
            verification.verification_status = JobVerificationStatus.VERIFIED
            verification.verified_at = datetime.now(UTC)
            verification.expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
            verification.rejection_reason = None
        else:
            verification.verification_status = JobVerificationStatus.REJECTED
            verification.rejection_reason = rejection_reason
        verification.reviewer_notes = reviewer_notes
        verification.reviewer_id = reviewer.id
        await self.audit.record(
            action="verification.review",
            actor_user_id=reviewer.id,
            entity_type="job_verification",
            entity_id=str(verification.id),
            metadata={"approved": approve},
        )
        return verification

    async def request_more_info(self, reviewer: User, verification_id: UUID, *, reason: str) -> JobVerification:
        """Request additional documents. Keeps the record visible in the queue."""
        verification = await self.session.get(JobVerification, verification_id)
        if verification is None:
            raise NotFoundError("Verification not found", code="VERIFICATION_NOT_FOUND")
        if verification.verification_status == JobVerificationStatus.PENDING_PAYMENT:
            raise ForbiddenError("Cannot request info before payment", code="VERIFICATION_NOT_PAID")
        verification.reviewer_notes = reason
        await self.audit.record(
            action="job_verification.info_requested",
            actor_user_id=reviewer.id,
            entity_type="job_verification",
            entity_id=str(verification.id),
            metadata={"reason": reason},
        )
        return verification

    async def list_by_status(self, status: JobVerificationStatus | None = None) -> list[JobVerification]:
        return await self.repo.list_by_status(status)
