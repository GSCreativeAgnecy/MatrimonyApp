from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UTCDateTime, enum_column, gen_uuid
from app.db.enums import EmploymentType, JobVerificationStatus


class JobVerification(Base, TimestampMixin):
    __tablename__ = "job_verifications"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    employment_type: Mapped[EmploymentType] = enum_column(EmploymentType, nullable=False)
    employer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    verification_status: Mapped[JobVerificationStatus] = enum_column(
        JobVerificationStatus, default=JobVerificationStatus.PENDING_PAYMENT, index=True
    )

    amount_paid: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    payment_id: Mapped[UUID | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)

    reviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "expires_at IS NULL OR verified_at IS NULL OR expires_at >= verified_at", name="ck_job_expiry"
        ),
        Index("ix_job_verifications_status", "verification_status"),
    )
