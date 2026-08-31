from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, JSONBType, UTCDateTime, enum_column, gen_uuid
from app.db.enums import NotificationCampaignStatus, NotificationChannel


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    data: Mapped[dict | None] = mapped_column(JSONBType, nullable=True, default=dict)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)


class NotificationCampaign(Base):
    """An admin-initiated broadcast campaign.

    The actual fan-out to users is performed by the ``send_notification_campaign``
    ARQ worker in batches — never synchronously inside the HTTP request.
    """

    __tablename__ = "notification_campaigns"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    channel: Mapped[NotificationChannel] = enum_column(
        NotificationChannel, default=NotificationChannel.PUSH, index=True
    )
    audience: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)

    status: Mapped[NotificationCampaignStatus] = enum_column(
        NotificationCampaignStatus, default=NotificationCampaignStatus.QUEUED, index=True
    )
    target_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False, index=True)
