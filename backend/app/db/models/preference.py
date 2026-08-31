from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, enum_column, gen_uuid
from app.db.enums import PreferenceLevel


class PartnerPreference(Base, TimestampMixin):
    __tablename__ = "partner_preferences"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    age_min: Mapped[int | None] = mapped_column(nullable=True)
    age_max: Mapped[int | None] = mapped_column(nullable=True)

    height_min_cm: Mapped[int | None] = mapped_column(nullable=True)
    height_max_cm: Mapped[int | None] = mapped_column(nullable=True)

    preferred_marital_status: Mapped[str | None] = mapped_column(nullable=True)
    preferred_physical_status: Mapped[str | None] = mapped_column(nullable=True)

    preferred_family_values: Mapped[str | None] = mapped_column(nullable=True)
    preferred_education: Mapped[str | None] = mapped_column(nullable=True)
    preferred_employed_in: Mapped[str | None] = mapped_column(nullable=True)

    # Preference levels for the multi-value lists
    religion_level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.NO_PREFERENCE)
    caste_level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.NO_PREFERENCE)
    language_level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.NO_PREFERENCE)
    country_level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.NO_PREFERENCE)
    state_level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.NO_PREFERENCE)
    diet_level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.NO_PREFERENCE)

    __table_args__ = (
        CheckConstraint("age_min IS NULL OR age_max IS NULL OR age_min <= age_max", name="age_range"),
        CheckConstraint(
            "height_min_cm IS NULL OR height_max_cm IS NULL OR height_min_cm <= height_max_cm",
            name="height_range",
        ),
        Index("ix_partner_preferences_user", "user_id"),
    )


class PreferredJunctionBase(Base):
    """Abstract base for multi-value preference junction tables."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    preference_id: Mapped[UUID] = mapped_column(ForeignKey("partner_preferences.id", ondelete="CASCADE"), index=True)
    level: Mapped[PreferenceLevel] = enum_column(PreferenceLevel, default=PreferenceLevel.PREFERRED)


class PreferredReligion(PreferredJunctionBase):
    __tablename__ = "preferred_religions"
    __table_args__ = (UniqueConstraint("preference_id", "religion", name="uq_pref_religion"),)

    religion: Mapped[str] = mapped_column(nullable=False)


class PreferredCaste(PreferredJunctionBase):
    __tablename__ = "preferred_castes"
    __table_args__ = (UniqueConstraint("preference_id", "caste", name="uq_pref_caste"),)

    caste: Mapped[str] = mapped_column(nullable=False)


class PreferredLanguage(PreferredJunctionBase):
    __tablename__ = "preferred_languages"
    __table_args__ = (UniqueConstraint("preference_id", "language", name="uq_pref_language"),)

    language: Mapped[str] = mapped_column(nullable=False)


class PreferredCountry(PreferredJunctionBase):
    __tablename__ = "preferred_countries"
    __table_args__ = (UniqueConstraint("preference_id", "country", name="uq_pref_country"),)

    country: Mapped[str] = mapped_column(nullable=False)


class PreferredState(PreferredJunctionBase):
    __tablename__ = "preferred_states"
    __table_args__ = (UniqueConstraint("preference_id", "state", name="uq_pref_state"),)

    state: Mapped[str] = mapped_column(nullable=False)


class PreferredDiet(PreferredJunctionBase):
    __tablename__ = "preferred_diets"
    __table_args__ = (UniqueConstraint("preference_id", "diet", name="uq_pref_diet"),)

    diet: Mapped[str] = mapped_column(nullable=False)
