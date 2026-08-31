from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, TimestampMixin, UTCDateTime, enum_column, gen_uuid
from app.db.enums import (
    BodyType,
    Complexion,
    Diet,
    Drinking,
    EmploymentStatus,
    Gender,
    Intent,
    MaritalStatus,
    PhysicalStatus,
    ProfileCreatedBy,
    ProfileReviewStatus,
    Smoking,
)


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    date_of_birth: Mapped[date | None] = mapped_column(nullable=True, index=True)
    gender: Mapped[Gender] = enum_column(Gender, nullable=True, index=True)

    bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    intent: Mapped[Intent] = enum_column(Intent, nullable=True, index=True)
    marital_status: Mapped[MaritalStatus] = enum_column(MaritalStatus, nullable=True, index=True)

    height_cm: Mapped[int | None] = mapped_column(nullable=True)
    body_type: Mapped[BodyType] = enum_column(BodyType, nullable=True)
    complexion: Mapped[Complexion] = enum_column(Complexion, nullable=True)
    physical_status: Mapped[PhysicalStatus] = enum_column(PhysicalStatus, nullable=True)

    diet: Mapped[Diet] = enum_column(Diet, nullable=True)
    drinking: Mapped[Drinking] = enum_column(Drinking, nullable=True)
    smoking: Mapped[Smoking] = enum_column(Smoking, nullable=True)

    mother_tongue: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    preferred_language: Mapped[str | None] = mapped_column(String(50), nullable=True)

    religion: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    caste: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    sub_caste: Mapped[str | None] = mapped_column(String(50), nullable=True)

    education: Mapped[str | None] = mapped_column(String(100), nullable=True)
    college: Mapped[str | None] = mapped_column(String(150), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(100), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(nullable=True)

    employment_status: Mapped[EmploymentStatus] = enum_column(EmploymentStatus, nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    workplace: Mapped[str | None] = mapped_column(String(150), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)

    annual_income: Mapped[int | None] = mapped_column(Numeric(14, 2), nullable=True)
    income_currency: Mapped[str | None] = mapped_column(String(3), nullable=True, default="INR")

    country: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    hometown: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Approximate coordinates for "distance" queries; never exposed via public API.
    location_lat: Mapped[float | None] = mapped_column(nullable=True)
    location_lng: Mapped[float | None] = mapped_column(nullable=True)
    location_updated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    profile_created_by: Mapped[ProfileCreatedBy] = enum_column(ProfileCreatedBy, default=ProfileCreatedBy.SELF)

    # Profile moderation (admin dashboard). Discovery integration is a documented
    # follow-up; these fields are a moderation ledger, not an enforcement point yet.
    review_status: Mapped[ProfileReviewStatus] = enum_column(
        ProfileReviewStatus, default=ProfileReviewStatus.PENDING, index=True
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    review_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user = relationship("User", back_populates="profile", uselist=False, foreign_keys=[user_id])

    __table_args__ = (
        CheckConstraint("height_cm IS NULL OR (height_cm BETWEEN 90 AND 250)", name="height_range"),
        CheckConstraint("location_lat IS NULL OR (location_lat BETWEEN -90 AND 90)", name="lat_range"),
        CheckConstraint("location_lng IS NULL OR (location_lng BETWEEN -180 AND 180)", name="lng_range"),
        Index("ix_profiles_discovery", "gender", "country", "city"),
    )


class UserPrivacySettings(Base, TimestampMixin):
    __tablename__ = "user_privacy_settings"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    show_online_status: Mapped[bool] = mapped_column(default=True, nullable=False)
    show_distance: Mapped[bool] = mapped_column(default=True, nullable=False)
    show_last_seen: Mapped[bool] = mapped_column(default=True, nullable=False)

    profile_visibility: Mapped[str] = mapped_column(String(20), default="PUBLIC", nullable=False)
    photo_visibility: Mapped[str] = mapped_column(String(20), default="PUBLIC", nullable=False)

    phone_visibility: Mapped[str] = mapped_column(String(20), default="NONE", nullable=False)
    email_visibility: Mapped[str] = mapped_column(String(20), default="NONE", nullable=False)

    allow_messages_from: Mapped[str] = mapped_column(String(20), default="MATCHES_ONLY", nullable=False)
    allow_match_requests: Mapped[bool] = mapped_column(default=True, nullable=False)
