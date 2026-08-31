from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    GUID,
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UTCDateTime,
    enum_column,
    gen_uuid,
)
from app.db.enums import AccountStatus, UserRole


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    phone_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    account_status: Mapped[AccountStatus] = enum_column(AccountStatus, default=AccountStatus.PENDING, index=True)
    role: Mapped[UserRole] = enum_column(UserRole, default=UserRole.USER, index=True)
    is_banned: Mapped[bool] = mapped_column(default=False, nullable=False)
    banned_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    # Admin suspension ledger.
    suspended_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    suspended_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    suspended_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    suspended_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)

    profile = relationship(
        "Profile", back_populates="user", uselist=False, lazy="selectin", foreign_keys="Profile.user_id"
    )

    __table_args__ = (Index("ix_users_active", "account_status", "deleted_at"),)

    def __repr__(self) -> str:
        return f"<User id={self.id} status={self.account_status}>"


class RefreshTokenRecord(Base):
    """Server-side record for refresh-token rotation + revocation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    replaced_by_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)
