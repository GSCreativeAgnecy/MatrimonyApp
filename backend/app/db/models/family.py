from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, enum_column, gen_uuid
from app.db.enums import FamilyType, FamilyValues, MaritalStatus


class Family(Base, TimestampMixin):
    __tablename__ = "families"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    family_type: Mapped[FamilyType] = enum_column(FamilyType, nullable=True)
    family_values: Mapped[FamilyValues] = enum_column(FamilyValues, nullable=True)
    about_family: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    family_location: Mapped[str | None] = mapped_column(String(150), nullable=True)


class FamilyMember(Base, TimestampMixin):
    __tablename__ = "family_members"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    relationship: Mapped[str] = mapped_column(String(50), nullable=False)  # FATHER/MOTHER/BROTHER/SISTER/OTHER
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    education: Mapped[str | None] = mapped_column(String(100), nullable=True)
    marital_status: Mapped[MaritalStatus] = enum_column(MaritalStatus, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "relationship", name="uq_family_member_role"),)
