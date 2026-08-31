from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import (
    GUID,
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UTCDateTime,
    enum_column,
    gen_uuid,
)
from app.db.enums import PhotoVerificationStatus, PhotoVisibility


class Photo(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "photos"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_profile_photo: Mapped[bool] = mapped_column(default=False, nullable=False)

    verification_status: Mapped[PhotoVerificationStatus] = enum_column(
        PhotoVerificationStatus, default=PhotoVerificationStatus.UNVERIFIED, index=True
    )

    visibility: Mapped[PhotoVisibility] = enum_column(PhotoVisibility, default=PhotoVisibility.PUBLIC)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_photos_user_position", "user_id", "position"),)
