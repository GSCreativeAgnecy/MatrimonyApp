from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, JSONBType, TimestampMixin, UTCDateTime, enum_column, gen_uuid
from app.db.enums import PaymentStatus, PaymentType, SubscriptionStatus


class SubscriptionPlan(Base, TimestampMixin):
    __tablename__ = "subscription_plans"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[dict | None] = mapped_column(JSONBType, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)

    status: Mapped[SubscriptionStatus] = enum_column(SubscriptionStatus, default=SubscriptionStatus.ACTIVE, index=True)

    starts_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    __table_args__ = (
        CheckConstraint("expires_at IS NULL OR expires_at >= starts_at", name="ck_subscription_range"),
        Index("ix_subscriptions_user_status", "user_id", "status"),
    )


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    payment_type: Mapped[PaymentType] = enum_column(PaymentType, nullable=False)
    status: Mapped[PaymentStatus] = enum_column(PaymentStatus, default=PaymentStatus.PENDING, index=True)

    provider: Mapped[str] = mapped_column(String(50), default="mock", nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)

    meta: Mapped[dict | None] = mapped_column("metadata", JSONBType, nullable=True, default=dict)

    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
