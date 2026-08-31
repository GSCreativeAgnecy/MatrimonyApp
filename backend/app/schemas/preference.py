from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.enums import PreferenceLevel


class PreferenceItem(BaseModel):
    value: str
    level: PreferenceLevel = PreferenceLevel.PREFERRED


class PartnerPreferenceUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    age_min: int | None = Field(default=None, ge=18, le=90)
    age_max: int | None = Field(default=None, ge=18, le=90)
    height_min_cm: int | None = Field(default=None, ge=90, le=250)
    height_max_cm: int | None = Field(default=None, ge=90, le=250)
    preferred_marital_status: str | None = None
    preferred_physical_status: str | None = None
    preferred_family_values: str | None = None
    preferred_education: str | None = None
    preferred_employed_in: str | None = None

    preferred_religions: list[PreferenceItem] | None = None
    preferred_castes: list[PreferenceItem] | None = None
    preferred_languages: list[PreferenceItem] | None = None
    preferred_countries: list[PreferenceItem] | None = None
    preferred_states: list[PreferenceItem] | None = None
    preferred_diets: list[PreferenceItem] | None = None

    @model_validator(mode="after")
    def _valid_ranges(self) -> "PartnerPreferenceUpdate":
        if self.age_min is not None and self.age_max is not None and self.age_min > self.age_max:
            raise ValueError("age_min must be <= age_max")
        if (
            self.height_min_cm is not None
            and self.height_max_cm is not None
            and self.height_min_cm > self.height_max_cm
        ):
            raise ValueError("height_min_cm must be <= height_max_cm")
        return self


class PartnerPreferenceResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    age_min: int | None = None
    age_max: int | None = None
    height_min_cm: int | None = None
    height_max_cm: int | None = None
    preferred_marital_status: str | None = None
    preferred_physical_status: str | None = None
    preferred_family_values: str | None = None
    preferred_education: str | None = None
    preferred_employed_in: str | None = None
    preferred_religions: list[PreferenceItem] = []
    preferred_castes: list[PreferenceItem] = []
    preferred_languages: list[PreferenceItem] = []
    preferred_countries: list[PreferenceItem] = []
    preferred_states: list[PreferenceItem] = []
    preferred_diets: list[PreferenceItem] = []
