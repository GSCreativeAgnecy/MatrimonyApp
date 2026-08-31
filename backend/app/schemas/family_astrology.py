from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.enums import AstrologyRashi, Dosham, Nakshatra


class AstrologyUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    time_of_birth: str | None = None
    place_of_birth: str | None = None
    birth_lat: float | None = None
    birth_lng: float | None = None
    birth_timezone: str | None = None
    rashi: AstrologyRashi | None = None
    nakshatra: Nakshatra | None = None
    gothram: str | None = None
    dosham: Dosham | None = None


class AstrologyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    time_of_birth: datetime | None = None
    place_of_birth: str | None = None
    rashi: str | None = None
    nakshatra: str | None = None
    gothram: str | None = None
    dosham: str | None = None
    horoscope_verified: bool


class AstrologyProviderProto(BaseModel):
    """Contract shape for an astrology provider result."""

    rashi: str | None = None
    nakshatra: str | None = None
    gothram: str | None = None
    dosham: str | None = None
    horoscope_data: dict = {}


class FamilyUpdate(BaseModel):
    family_type: str | None = None
    family_values: str | None = None
    about_family: str | None = None
    family_location: str | None = None


class FamilyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    family_type: str | None = None
    family_values: str | None = None
    about_family: str | None = None
    family_location: str | None = None


class FamilyMemberCreate(BaseModel):
    relationship: str
    name: str | None = None
    occupation: str | None = None
    education: str | None = None
    marital_status: str | None = None


class FamilyMemberUpdate(BaseModel):
    name: str | None = None
    occupation: str | None = None
    education: str | None = None
    marital_status: str | None = None


class FamilyMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    relationship: str
    name: str | None = None
    occupation: str | None = None
    education: str | None = None
    marital_status: str | None = None
