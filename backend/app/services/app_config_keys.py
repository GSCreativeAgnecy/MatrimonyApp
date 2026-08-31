"""Central registry of known remote-configuration keys.

Every key the mobile app or the server relies on is declared here so that key
names, categories, value types, visibility and defaults stay in one place
instead of being hardcoded across the codebase.

The registry is the single source of truth used by:
  * seed data generation (``app.seed``),
  * the public/admin app-config services (validation, grouping, defaults).
"""

from dataclasses import dataclass
from typing import Any

from app.config.settings import settings
from app.db.enums import ConfigCategory, ConfigValueType


@dataclass(frozen=True)
class ConfigKeySpec:
    key: str
    value_type: ConfigValueType
    category: ConfigCategory
    is_public: bool = True
    default: Any = None
    description: str = ""


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
BRANDING_APP_NAME = "branding.app_name"
BRANDING_TAGLINE = "branding.tagline"
BRANDING_LOGO_URL = "branding.logo_url"
BRANDING_DARK_LOGO_URL = "branding.dark_logo_url"
BRANDING_PRIMARY_COLOR = "branding.primary_color"
BRANDING_SECONDARY_COLOR = "branding.secondary_color"
BRANDING_BACKGROUND_COLOR = "branding.background_color"
BRANDING_TEXT_COLOR = "branding.text_color"
BRANDING_ACCENT_COLOR = "branding.accent_color"

# ---------------------------------------------------------------------------
# App / maintenance
# ---------------------------------------------------------------------------
APP_MAINTENANCE_MODE = "app.maintenance_mode"
APP_MAINTENANCE_MESSAGE = "app.maintenance_message"

# ---------------------------------------------------------------------------
# Features (UI/UX flags only — never authorization)
# ---------------------------------------------------------------------------
FEATURES_REGISTRATION = "features.enable_registration"
FEATURES_SWIPING = "features.enable_swiping"
FEATURES_MESSAGING = "features.enable_messaging"
FEATURES_ASTROLOGY = "features.enable_astrology"
FEATURES_JOB_VERIFICATION = "features.enable_job_verification"
FEATURES_FAMILY_SHARING = "features.enable_family_sharing"
FEATURES_VIDEO_CALLS = "features.enable_video_calls"
FEATURES_PREMIUM = "features.enable_premium"

# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------
LIMITS_MAX_PHOTOS = "limits.max_photos"
LIMITS_MAX_DAILY_SWIPES = "limits.max_daily_swipes"
LIMITS_MAX_PROFILE_IMAGES = "limits.max_profile_images"

# ---------------------------------------------------------------------------
# Pricing (display only — authoritative pricing is always read server-side)
# ---------------------------------------------------------------------------
PRICING_LOCAL_JOB_VERIFICATION = "pricing.local_job_verification"
PRICING_NRI_JOB_VERIFICATION = "pricing.nri_job_verification"

# ---------------------------------------------------------------------------
# Versions / force update
# ---------------------------------------------------------------------------
VERSIONS_MIN_IOS = "app.minimum_ios_version"
VERSIONS_MIN_ANDROID = "app.minimum_android_version"
VERSIONS_LATEST_IOS = "app.latest_ios_version"
VERSIONS_LATEST_ANDROID = "app.latest_android_version"
VERSIONS_FORCE_UPDATE_IOS = "app.force_update_ios"
VERSIONS_FORCE_UPDATE_ANDROID = "app.force_update_android"

# ---------------------------------------------------------------------------
# Legal / support
# ---------------------------------------------------------------------------
LEGAL_PRIVACY_URL = "app.privacy_url"
LEGAL_TERMS_URL = "app.terms_url"
LEGAL_CONTACT_URL = "app.contact_url"
SUPPORT_EMAIL = "app.support_email"
SUPPORT_PHONE = "app.support_phone"

# Legacy keys retained for backward compatibility when reading pricing.
LEGACY_PRICE_KEYS = {"LOCAL_JOB_VERIFICATION_PRICE", "NRI_JOB_VERIFICATION_PRICE"}

# Legacy lookup map: legacy key -> current pricing key.
LEGACY_TO_CURRENT_PRICE = {
    "LOCAL_JOB_VERIFICATION_PRICE": PRICING_LOCAL_JOB_VERIFICATION,
    "NRI_JOB_VERIFICATION_PRICE": PRICING_NRI_JOB_VERIFICATION,
}


CONFIG_KEY_SPECS: dict[str, ConfigKeySpec] = {
    spec.key: spec
    for spec in [
        # Branding
        ConfigKeySpec(
            BRANDING_APP_NAME,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="MyMatrimony",
            description="Application display name",
        ),
        ConfigKeySpec(
            BRANDING_TAGLINE,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="Find your perfect match",
            description="Application tagline",
        ),
        ConfigKeySpec(
            BRANDING_LOGO_URL,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default=None,
            description="Light theme logo URL",
        ),
        ConfigKeySpec(
            BRANDING_DARK_LOGO_URL,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default=None,
            description="Dark theme logo URL",
        ),
        ConfigKeySpec(
            BRANDING_PRIMARY_COLOR,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="#7C3AED",
            description="Primary brand color (hex)",
        ),
        ConfigKeySpec(
            BRANDING_SECONDARY_COLOR,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="#EC4899",
            description="Secondary brand color (hex)",
        ),
        ConfigKeySpec(
            BRANDING_BACKGROUND_COLOR,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="#FFFFFF",
            description="Background color (hex)",
        ),
        ConfigKeySpec(
            BRANDING_TEXT_COLOR,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="#000000",
            description="Text color (hex)",
        ),
        ConfigKeySpec(
            BRANDING_ACCENT_COLOR,
            ConfigValueType.STRING,
            ConfigCategory.BRANDING,
            default="#7C3AED",
            description="Accent color (hex)",
        ),
        # App / maintenance
        ConfigKeySpec(
            APP_MAINTENANCE_MODE,
            ConfigValueType.BOOLEAN,
            ConfigCategory.APP,
            default=False,
            description="When true the app shows the maintenance screen",
        ),
        ConfigKeySpec(
            APP_MAINTENANCE_MESSAGE,
            ConfigValueType.STRING,
            ConfigCategory.APP,
            default=None,
            description="Optional maintenance message",
        ),
        # Features (UI flags only)
        ConfigKeySpec(
            FEATURES_REGISTRATION,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide registration UI",
        ),
        ConfigKeySpec(
            FEATURES_SWIPING,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide swipe UI",
        ),
        ConfigKeySpec(
            FEATURES_MESSAGING,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide messaging UI",
        ),
        ConfigKeySpec(
            FEATURES_ASTROLOGY,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide astrology UI",
        ),
        ConfigKeySpec(
            FEATURES_JOB_VERIFICATION,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide job verification UI",
        ),
        ConfigKeySpec(
            FEATURES_FAMILY_SHARING,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide family sharing UI",
        ),
        ConfigKeySpec(
            FEATURES_VIDEO_CALLS,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=False,
            description="Show/hide video calls UI",
        ),
        ConfigKeySpec(
            FEATURES_PREMIUM,
            ConfigValueType.BOOLEAN,
            ConfigCategory.FEATURES,
            default=True,
            description="Show/hide premium UI",
        ),
        # Limits
        ConfigKeySpec(
            LIMITS_MAX_PHOTOS,
            ConfigValueType.INTEGER,
            ConfigCategory.LIMITS,
            default=6,
            description="Maximum photo count",
        ),
        ConfigKeySpec(
            LIMITS_MAX_DAILY_SWIPES,
            ConfigValueType.INTEGER,
            ConfigCategory.LIMITS,
            default=50,
            description="Maximum swipes per day",
        ),
        ConfigKeySpec(
            LIMITS_MAX_PROFILE_IMAGES,
            ConfigValueType.INTEGER,
            ConfigCategory.LIMITS,
            default=6,
            description="Maximum profile images",
        ),
        # Pricing (display only)
        ConfigKeySpec(
            PRICING_LOCAL_JOB_VERIFICATION,
            ConfigValueType.INTEGER,
            ConfigCategory.PRICING,
            default=int(settings.LOCAL_JOB_VERIFICATION_PRICE),
            description="Local job verification price",
        ),
        ConfigKeySpec(
            PRICING_NRI_JOB_VERIFICATION,
            ConfigValueType.INTEGER,
            ConfigCategory.PRICING,
            default=int(settings.NRI_JOB_VERIFICATION_PRICE),
            description="NRI job verification price",
        ),
        # Versions
        ConfigKeySpec(
            VERSIONS_MIN_IOS,
            ConfigValueType.STRING,
            ConfigCategory.VERSIONS,
            default="1.0.0",
            description="Minimum supported iOS version",
        ),
        ConfigKeySpec(
            VERSIONS_MIN_ANDROID,
            ConfigValueType.STRING,
            ConfigCategory.VERSIONS,
            default="1.0.0",
            description="Minimum supported Android version",
        ),
        ConfigKeySpec(
            VERSIONS_LATEST_IOS,
            ConfigValueType.STRING,
            ConfigCategory.VERSIONS,
            default="1.0.0",
            description="Latest iOS version",
        ),
        ConfigKeySpec(
            VERSIONS_LATEST_ANDROID,
            ConfigValueType.STRING,
            ConfigCategory.VERSIONS,
            default="1.0.0",
            description="Latest Android version",
        ),
        ConfigKeySpec(
            VERSIONS_FORCE_UPDATE_IOS,
            ConfigValueType.BOOLEAN,
            ConfigCategory.VERSIONS,
            default=False,
            description="Force iOS update",
        ),
        ConfigKeySpec(
            VERSIONS_FORCE_UPDATE_ANDROID,
            ConfigValueType.BOOLEAN,
            ConfigCategory.VERSIONS,
            default=False,
            description="Force Android update",
        ),
        # Legal / support
        ConfigKeySpec(
            LEGAL_PRIVACY_URL,
            ConfigValueType.STRING,
            ConfigCategory.LEGAL,
            default=None,
            description="Privacy policy URL",
        ),
        ConfigKeySpec(
            LEGAL_TERMS_URL,
            ConfigValueType.STRING,
            ConfigCategory.LEGAL,
            default=None,
            description="Terms of service URL",
        ),
        ConfigKeySpec(
            LEGAL_CONTACT_URL,
            ConfigValueType.STRING,
            ConfigCategory.LEGAL,
            default=None,
            description="Contact page URL",
        ),
        ConfigKeySpec(
            SUPPORT_EMAIL,
            ConfigValueType.STRING,
            ConfigCategory.SUPPORT,
            default=None,
            description="Support email address",
        ),
        ConfigKeySpec(
            SUPPORT_PHONE,
            ConfigValueType.STRING,
            ConfigCategory.SUPPORT,
            default=None,
            description="Support phone number",
        ),
    ]
}

# Keys whose string values must be valid hex colors.
COLOR_KEYS = frozenset(key for key, spec in CONFIG_KEY_SPECS.items() if key.endswith("_color"))

# Well-known categories that may carry private entries.
KNOWN_CATEGORIES = frozenset(spec.category for spec in CONFIG_KEY_SPECS.values())

# Public grouping key per category (stable for clients).
CATEGORY_GROUP = {category: category.value.lower() for category in ConfigCategory}


def spec_for_key(key: str) -> ConfigKeySpec | None:
    return CONFIG_KEY_SPECS.get(key)


def public_name_for(key: str) -> str:
    """Map a database key to the stable public field name in the grouped payload.

    Database keys use ``enable_*`` prefixes (per the key registry) while the
    public schema exposes friendlier names (e.g. ``features.registration``) and
    folds the ``app.support_*`` keys into the ``support`` group.
    """
    sub = key.split(".", 1)[1]
    if key.startswith("features."):
        return sub.removeprefix("enable_")
    if key == SUPPORT_EMAIL:
        return "email"
    if key == SUPPORT_PHONE:
        return "phone"
    return sub
