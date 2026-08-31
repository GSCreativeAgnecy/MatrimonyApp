"""All models, imported so the metadata registry is fully populated."""

from app.db.base import Base
from app.db.models.admin import RecoveryCode, RolePermission, UserTotpSecret
from app.db.models.astrology import AstrologyProfile
from app.db.models.audit import AuditLog
from app.db.models.billing import Payment, Subscription, SubscriptionPlan
from app.db.models.family import Family, FamilyMember
from app.db.models.lookups import (
    AppConfig,
    Caste,
    Country,
    EducationLevel,
    Interest,
    Language,
    Occupation,
    Religion,
    State,
    UserInterest,
    UserLanguage,
)
from app.db.models.match import Match
from app.db.models.message import Conversation, ConversationParticipant, Message
from app.db.models.moderation import Block, Report
from app.db.models.notification import Notification, NotificationCampaign
from app.db.models.photo import Photo
from app.db.models.preference import (
    PartnerPreference,
    PreferredCaste,
    PreferredCountry,
    PreferredDiet,
    PreferredJunctionBase,
    PreferredLanguage,
    PreferredReligion,
    PreferredState,
)
from app.db.models.profile import Profile, UserPrivacySettings
from app.db.models.share import ProfileShare
from app.db.models.swipe import Swipe
from app.db.models.user import RefreshTokenRecord, User
from app.db.models.verification import JobVerification

all_models = Base

__all__ = [
    "AppConfig",
    "AstrologyProfile",
    "AuditLog",
    "Base",
    "Block",
    "Caste",
    "Conversation",
    "ConversationParticipant",
    "Country",
    "EducationLevel",
    "Family",
    "FamilyMember",
    "Interest",
    "JobVerification",
    "Language",
    "Match",
    "Message",
    "Notification",
    "NotificationCampaign",
    "Occupation",
    "PartnerPreference",
    "Payment",
    "Photo",
    "PreferredCaste",
    "PreferredCountry",
    "PreferredDiet",
    "PreferredJunctionBase",
    "PreferredLanguage",
    "PreferredReligion",
    "PreferredState",
    "Profile",
    "ProfileShare",
    "RecoveryCode",
    "RefreshTokenRecord",
    "Religion",
    "Report",
    "RolePermission",
    "State",
    "Subscription",
    "SubscriptionPlan",
    "Swipe",
    "User",
    "UserInterest",
    "UserLanguage",
    "UserPrivacySettings",
    "UserTotpSecret",
    "all_models",
]
