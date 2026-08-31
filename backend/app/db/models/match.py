from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UTCDateTime, enum_column, gen_uuid
from app.db.enums import MatchStatus


class Match(Base, TimestampMixin):
    __tablename__ = "matches"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)

    # Normalized ordering: user1_id < user2_id always, so no mirrored duplicates.
    user1_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[MatchStatus] = enum_column(MatchStatus, default=MatchStatus.ACTIVE, index=True)

    matched_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)
    unmatched_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_match_pair"),
        CheckConstraint("user1_id < user2_id", name="ck_match_normalized_order"),
        Index("ix_matches_user_status", "user1_id", "status"),
        Index("ix_matches_user2_status", "user2_id", "status"),
    )
