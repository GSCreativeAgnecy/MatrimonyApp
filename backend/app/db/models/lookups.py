from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, Base, JSONBType, TimestampMixin, enum_column, gen_uuid
from app.db.enums import ConfigCategory, ConfigValueType


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class UserLanguage(Base):
    __tablename__ = "user_languages"
    __table_args__ = (UniqueConstraint("user_id", "language_id", name="uq_user_language"),)

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    language_id: Mapped[UUID] = mapped_column(ForeignKey("languages.id", ondelete="CASCADE"), nullable=False)
    is_native: Mapped[bool] = mapped_column(default=False, nullable=False)
    proficiency: Mapped[str] = mapped_column(String(20), default="FLUENT", nullable=False)

    language: Mapped[Language] = relationship("Language", lazy="joined")


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class UserInterest(Base):
    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "interest_id", name="uq_user_interest"),)

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interest_id: Mapped[UUID] = mapped_column(ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)

    interest: Mapped[Interest] = relationship("Interest", lazy="joined")


class Religion(Base):
    __tablename__ = "religions"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Caste(Base):
    __tablename__ = "castes"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    religion: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("religion", "name", name="uq_caste_religion_name"),)


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class State(Base):
    __tablename__ = "states"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("country_code", "name", name="uq_state_country_name"),)


class EducationLevel(Base):
    __tablename__ = "education_levels"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Occupation(Base):
    __tablename__ = "occupations"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AppConfig(Base, TimestampMixin):
    """Database-driven key/value configuration for the mobile application and server.

    Public entries are served to clients via ``GET /api/v1/app/config`` (grouped by
    category). Private entries are only visible through admin endpoints. This table
    is NOT a secret store — secrets live in environment variables.
    """

    __tablename__ = "app_config"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    value: Mapped[Any] = mapped_column(JSONBType, nullable=False)
    value_type: Mapped[ConfigValueType] = enum_column(ConfigValueType, default=ConfigValueType.STRING, nullable=False)
    category: Mapped[ConfigCategory] = enum_column(
        ConfigCategory, default=ConfigCategory.APP, nullable=False, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
