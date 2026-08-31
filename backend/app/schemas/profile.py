from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.enums import (
    BodyType,
    Complexion,
    Diet,
    Drinking,
    EmploymentStatus,
    Gender,
    Intent,
    MaritalStatus,
    PhysicalStatus,
    ProfileCreatedBy,
    Smoking,
)


class ProfileBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    gender: Gender | None = None
    bio: str | None = Field(default=None, max_length=1000)
    intent: Intent | None = None
    marital_status: MaritalStatus | None = None
    height_cm: int | None = Field(default=None, ge=90, le=250)
    body_type: BodyType | None = None
    complexion: Complexion | None = None
    physical_status: PhysicalStatus | None = None
    diet: Diet | None = None
    drinking: Drinking | None = None
    smoking: Smoking | None = None
    mother_tongue: str | None = Field(default=None, max_length=50)
    preferred_language: str | None = Field(default=None, max_length=50)
    religion: str | None = Field(default=None, max_length=50)
    caste: str | None = Field(default=None, max_length=50)
    sub_caste: str | None = Field(default=None, max_length=50)
    education: str | None = Field(default=None, max_length=100)
    college: str | None = Field(default=None, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=100)
    graduation_year: int | None = Field(default=None, ge=1960, le=2100)
    employment_status: EmploymentStatus | None = None
    occupation: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=100)
    workplace: str | None = Field(default=None, max_length=150)
    industry: str | None = Field(default=None, max_length=100)
    annual_income: int | None = Field(default=None, ge=0)
    income_currency: str | None = Field(default="INR", max_length=3)
    country: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    hometown: str | None = Field(default=None, max_length=150)
    profile_created_by: ProfileCreatedBy | None = None

    @field_validator("date_of_birth")
    @classmethod
    def _dob_in_past(cls, v: date | None) -> date | None:
        if v and v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return v


class ProfileCreate(ProfileBase):
    gender: Gender = Field(...)
    date_of_birth: date = Field(...)
    first_name: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def _valid_age(self) -> "ProfileCreate":
        if self.date_of_birth and (date.today().year - self.date_of_birth.year) < 18:
            raise ValueError("You must be at least 18 years old")
        return self


class ProfileUpdate(ProfileBase):
    pass


class PrivacySettingsUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    show_online_status: bool | None = None
    show_distance: bool | None = None
    show_last_seen: bool | None = None
    profile_visibility: Literal["PUBLIC", "PRIVATE"] | None = None
    photo_visibility: Literal["PUBLIC", "PRIVATE"] | None = None
    phone_visibility: Literal["NONE", "CONTACTS", "MATCHES", "EVERYONE"] | None = None
    email_visibility: Literal["NONE", "CONTACTS", "MATCHES", "EVERYONE"] | None = None
    allow_messages_from: Literal["EVERYONE", "MATCHES_ONLY", "NOBODY"] | None = None
    allow_match_requests: bool | None = None


class PrivacySettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    show_online_status: bool
    show_distance: bool
    show_last_seen: bool
    profile_visibility: str
    photo_visibility: str
    phone_visibility: str
    email_visibility: str
    allow_messages_from: str
    allow_match_requests: bool


class OwnProfileResponse(ProfileBase):
    """Full profile viewable only by the owner (or permitted admin)."""

    id: str
    user_id: str
    location_lat: float | None = None
    location_lng: float | None = None
    location_updated_at: str | None = None
    privacy: PrivacySettingsResponse | None = None
    profile_photo: str | None = None
    photo_count: int = 0
    created_at: str | None = None


class PublicProfileResponse(BaseModel):
    """Safe fields for a public (not-matched) viewer. No contact/income/DOB/location detail."""

    id: str
    user_id: str
    first_name: str | None = None
    gender: str | None = None
    age: int | None = None
    marital_status: str | None = None
    religion: str | None = None
    caste: str | None = None
    mother_tongue: str | None = None
    education: str | None = None
    occupation: str | None = None
    job_title: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    distance_km: float | None = None
    bio: str | None = None
    intent: str | None = None
    diet: str | None = None
    drinking: str | None = None
    smoking: str | None = None
    height_cm: int | None = None
    body_type: str | None = None
    profile_photo: str | None = None
    last_seen: str | None = None
    is_online: bool = False
    is_verified_photo: bool = False
    is_verified_job: bool = False


class MatchedProfileResponse(PublicProfileResponse):
    """Adds contact details unlocked only for matched users."""

    phone_number: str | None = None
    email: str | None = None
    workplace: str | None = None


class AdminProfileResponse(OwnProfileResponse):
    phone_number: str | None = None
    email: str | None = None
    annual_income: int | None = None
    family: dict | None = None
    horoscope: dict | None = None
