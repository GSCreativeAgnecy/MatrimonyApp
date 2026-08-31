from uuid import UUID

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, enum_column, gen_uuid
from app.db.enums import SwipeAction


class Swipe(Base, TimestampMixin):
    __tablename__ = "swipes"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    from_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action: Mapped[SwipeAction] = enum_column(SwipeAction, nullable=False)

    # Only one LIKE / SUPER_LIKE per pair is allowed (multiple PASS rows are fine).
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", "action", name="uq_swipe_active_unique"),
        Index("ix_swipes_from_created", "from_user_id", "created_at"),
        Index("ix_swipes_to_from", "to_user_id", "from_user_id"),
    )
