from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UTCDateTime, gen_uuid


class RolePermission(Base, TimestampMixin):
    """Maps an admin role to a granted permission string.

    The default mapping (``ROLE_PERMISSIONS`` in ``app.security.permissions``)
    is seeded here so a SUPER_ADMIN can adjust it at runtime. ``require_permission``
    checks this table, falling back to the static registry when it is empty.
    """

    __tablename__ = "role_permissions"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("role", "permission", name="uq_role_permission"),)


class UserTotpSecret(Base, TimestampMixin):
    """TOTP (RFC 6238) secret for two-factor authentication (opt-in)."""

    __tablename__ = "user_totp_secrets"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class RecoveryCode(Base):
    """Single-use recovery code that bypasses TOTP (stored as a hash only)."""

    __tablename__ = "totp_recovery_codes"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)
