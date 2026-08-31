from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UTCDateTime, enum_column, gen_uuid
from app.db.enums import SharePermission


class ProfileShare(Base, TimestampMixin):
    __tablename__ = "profile_shares"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "shared_with_user_id", name="uq_profile_share"),
        Index("ix_profile_shares_owner", "owner_user_id"),
        Index("ix_profile_shares_shared_with", "shared_with_user_id"),
    )

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    permission: Mapped[SharePermission] = enum_column(SharePermission, default=SharePermission.VIEW)

    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
