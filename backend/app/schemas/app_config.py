from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import ConfigCategory, ConfigValueType

PUBLIC_CONFIG_KEYS = {
    "branding": [
        "app_name",
        "tagline",
        "logo_url",
        "dark_logo_url",
        "primary_color",
        "secondary_color",
        "background_color",
        "text_color",
        "accent_color",
    ],
    "app": ["maintenance_mode", "maintenance_message"],
    "features": [
        "registration",
        "swiping",
        "messaging",
        "astrology",
        "job_verification",
        "family_sharing",
        "video_calls",
        "premium",
    ],
    "limits": ["max_photos", "max_daily_swipes", "max_profile_images"],
    "pricing": ["local_job_verification", "nri_job_verification"],
    "versions": [
        "minimum_ios_version",
        "minimum_android_version",
        "latest_ios_version",
        "latest_android_version",
        "force_update_ios",
        "force_update_android",
    ],
    "legal": ["privacy_url", "terms_url", "contact_url"],
    "support": ["email", "phone"],
}


class _ConfigGroup(BaseModel):
    """Base for public config groups.

    ``extra="allow"`` lets additional keys be added later without breaking older
    clients — unknown keys are simply carried through the JSON payload.
    """

    model_config = ConfigDict(extra="allow")


class BrandingConfig(_ConfigGroup):
    app_name: str | None = None
    tagline: str | None = None
    logo_url: str | None = None
    dark_logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    background_color: str | None = None
    text_color: str | None = None
    accent_color: str | None = None


class AppGroupConfig(_ConfigGroup):
    maintenance_mode: bool = False
    maintenance_message: str | None = None


class FeatureConfig(_ConfigGroup):
    registration: bool = True
    swiping: bool = True
    messaging: bool = True
    astrology: bool = True
    job_verification: bool = True
    family_sharing: bool = True
    video_calls: bool = False
    premium: bool = True


class LimitsConfig(_ConfigGroup):
    max_photos: int | None = None
    max_daily_swipes: int | None = None
    max_profile_images: int | None = None


class PricingConfig(_ConfigGroup):
    local_job_verification: int | None = None
    nri_job_verification: int | None = None


class VersionConfig(_ConfigGroup):
    minimum_ios_version: str | None = None
    minimum_android_version: str | None = None
    latest_ios_version: str | None = None
    latest_android_version: str | None = None
    force_update_ios: bool = False
    force_update_android: bool = False


class LegalConfig(_ConfigGroup):
    privacy_url: str | None = None
    terms_url: str | None = None
    contact_url: str | None = None


class SupportConfig(_ConfigGroup):
    email: str | None = None
    phone: str | None = None


class PublicAppConfigResponse(BaseModel):
    """Grouped public configuration returned to the mobile app."""

    model_config = ConfigDict(extra="allow")

    branding: BrandingConfig = BrandingConfig()
    app: AppGroupConfig = AppGroupConfig()
    features: FeatureConfig = FeatureConfig()
    limits: LimitsConfig = LimitsConfig()
    pricing: PricingConfig = PricingConfig()
    versions: VersionConfig = VersionConfig()
    legal: LegalConfig = LegalConfig()
    support: SupportConfig = SupportConfig()


# --------------------------------------------------------------------------- admin


class AppConfigCreate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    key: str = Field(min_length=3, max_length=120)
    value: Any
    value_type: ConfigValueType = ConfigValueType.STRING
    category: ConfigCategory = ConfigCategory.APP
    is_public: bool = True
    is_active: bool = True
    description: str | None = Field(default=None, max_length=1000)


class AppConfigUpdate(BaseModel):
    """Value/visibility updates. ``key`` and ``value_type`` are immutable."""

    value: Any = None
    is_public: bool | None = None
    is_active: bool | None = None
    description: str | None = None
    category: ConfigCategory | None = None


class AppConfigAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    value: Any
    value_type: str
    category: str
    is_public: bool
    is_active: bool
    description: str | None = None
    updated_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
