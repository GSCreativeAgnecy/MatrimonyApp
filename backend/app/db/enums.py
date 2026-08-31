from enum import StrEnum


class AccountStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    DELETED = "DELETED"


class UserRole(StrEnum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    VERIFIER = "VERIFIER"
    SUPPORT = "SUPPORT"
    FINANCE = "FINANCE"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


# Roles that are allowed to sign in to the admin dashboard.
ADMIN_ROLES = frozenset(
    {
        UserRole.MODERATOR,
        UserRole.VERIFIER,
        UserRole.SUPPORT,
        UserRole.FINANCE,
        UserRole.ANALYST,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    }
)


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class MaritalStatus(StrEnum):
    NEVER_MARRIED = "NEVER_MARRIED"
    DIVORCED = "DIVORCED"
    WIDOWED = "WIDOWED"
    AWAITING_DIVORCE = "AWAITING_DIVORCE"


class Diet(StrEnum):
    VEGETARIAN = "VEGETARIAN"
    NON_VEGETARIAN = "NON_VEGETARIAN"
    EGGITARIAN = "EGGITARIAN"
    JAIN = "JAIN"
    VEGAN = "VEGAN"


class Drinking(StrEnum):
    NEVER = "NEVER"
    OCCASIONALLY = "OCCASIONALLY"
    REGULARLY = "REGULARLY"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class Smoking(StrEnum):
    NEVER = "NEVER"
    OCCASIONALLY = "OCCASIONALLY"
    REGULARLY = "REGULARLY"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class PhysicalStatus(StrEnum):
    NORMAL = "NORMAL"
    PHYSICALLY_CHALLENGED = "PHYSICALLY_CHALLENGED"


class EmploymentStatus(StrEnum):
    EMPLOYED = "EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    BUSINESS_OWNER = "BUSINESS_OWNER"
    STUDENT = "STUDENT"
    NOT_WORKING = "NOT_WORKING"
    RETIRED = "RETIRED"
    HOMEMAKER = "HOMEMAKER"


class Intent(StrEnum):
    MARRIAGE = "MARRIAGE"
    FRIENDSHIP = "FRIENDSHIP"
    DATE = "DATE"
    NOT_SURE = "NOT_SURE"


class ProfileCreatedBy(StrEnum):
    SELF = "SELF"
    PARENT = "PARENT"
    GUARDIAN = "GUARDIAN"
    RELATIVE = "RELATIVE"
    FRIEND = "FRIEND"
    PROFILE_SERVICE = "PROFILE_SERVICE"


class BodyType(StrEnum):
    SLIM = "SLIM"
    AVERAGE = "AVERAGE"
    ATHLETIC = "ATHLETIC"
    HEAVY = "HEAVY"


class Complexion(StrEnum):
    VERY_FAIR = "VERY_FAIR"
    FAIR = "FAIR"
    WHEATISH = "WHEATISH"
    MIDDLE_BROWN = "MIDDLE_BROWN"
    DARK = "DARK"


class PhotoVerificationStatus(StrEnum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class PhotoVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class PreferenceLevel(StrEnum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    NO_PREFERENCE = "NO_PREFERENCE"


class SwipeAction(StrEnum):
    LIKE = "LIKE"
    PASS = "PASS"
    SUPER_LIKE = "SUPER_LIKE"


class MatchStatus(StrEnum):
    ACTIVE = "ACTIVE"
    UNMATCHED = "UNMATCHED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


class MessageType(StrEnum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    SYSTEM = "SYSTEM"


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    ESCALATED = "ESCALATED"


class ReportReason(StrEnum):
    FAKE_PROFILE = "FAKE_PROFILE"
    SCAM = "SCAM"
    HARASSMENT = "HARASSMENT"
    INAPPROPRIATE_CONTENT = "INAPPROPRIATE_CONTENT"
    SPAM = "SPAM"
    UNDERAGE = "UNDERAGE"
    IMPERSONATION = "IMPERSONATION"
    OTHER = "OTHER"


class NotificationType(StrEnum):
    NEW_MATCH = "NEW_MATCH"
    NEW_MESSAGE = "NEW_MESSAGE"
    NEW_LIKE = "NEW_LIKE"
    PROFILE_VIEW = "PROFILE_VIEW"
    VERIFICATION_COMPLETE = "VERIFICATION_COMPLETE"
    SUBSCRIPTION_EXPIRING = "SUBSCRIPTION_EXPIRING"
    SYSTEM = "SYSTEM"


class SubscriptionStatus(StrEnum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class PaymentType(StrEnum):
    SUBSCRIPTION = "SUBSCRIPTION"
    JOB_VERIFICATION = "JOB_VERIFICATION"
    OTHER = "OTHER"


class JobVerificationStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class EmploymentType(StrEnum):
    LOCAL = "LOCAL"
    NRI = "NRI"


class SharePermission(StrEnum):
    VIEW = "VIEW"
    CONTACT = "CONTACT"
    MANAGE = "MANAGE"


class FamilyType(StrEnum):
    JOINT = "JOINT"
    NUCLEAR = "NUCLEAR"
    EXTENDED = "EXTENDED"


class FamilyValues(StrEnum):
    TRADITIONAL = "TRADITIONAL"
    MODERATE = "MODERATE"
    LIBERAL = "LIBERAL"
    ORTHODOX = "ORTHODOX"


class Dosham(StrEnum):
    NONE = "NONE"
    MANGAL = "MANGAL"
    PARTHIV = "PARTHIV"
    OTHER = "OTHER"


class AstrologyRashi(StrEnum):
    MESHA = "MESHA"
    VRISHABHA = "VRISHABHA"
    MITHUNA = "MITHUNA"
    KARKA = "KARKA"
    SIMHA = "SIMHA"
    KANYA = "KANYA"
    TULA = "TULA"
    VRISHCHIKA = "VRISHCHIKA"
    DHANU = "DHANU"
    MAKARA = "MAKARA"
    KUMBHA = "KUMBHA"
    MEENA = "MEENA"


class Nakshatra(StrEnum):
    ASHWINI = "ASHWINI"
    BHARANI = "BHARANI"
    KRITTIKA = "KRITTIKA"
    ROHINI = "ROHINI"
    MRIGASHIRA = "MRIGASHIRA"
    ARDRA = "ARDRA"
    PUNARVASU = "PUNARVASU"
    PUSHYA = "PUSHYA"
    ASHLESHA = "ASHLESHA"
    MAGHA = "MAGHA"
    PURVA_PHALGUNI = "PURVA_PHALGUNI"
    UTTARA_PHALGUNI = "UTTARA_PHALGUNI"
    HASTA = "HASTA"
    CHITRA = "CHITRA"
    SWATI = "SWATI"
    VISHAKHA = "VISHAKHA"
    ANURADHA = "ANURADHA"
    JYESHTHA = "JYESHTHA"
    MOOLA = "MOOLA"
    PURVA_ASHADHA = "PURVA_ASHADHA"
    UTTARA_ASHADHA = "UTTARA_ASHADHA"
    SHRAVANA = "SHRAVANA"
    DHANISHTA = "DHANISHTA"
    SHATABHISHA = "SHATABHISHA"
    PURVA_BHADRAPADA = "PURVA_BHADRAPADA"
    UTTARA_BHADRAPADA = "UTTARA_BHADRAPADA"
    REVATI = "REVATI"


class ProfileVisibility(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class MessageVisibility(StrEnum):
    EVERYONE = "EVERYONE"
    MATCHES_ONLY = "MATCHES_ONLY"
    NOBODY = "NOBODY"


class ConfigValueType(StrEnum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"


class ConfigCategory(StrEnum):
    BRANDING = "BRANDING"
    APP = "APP"
    FEATURES = "FEATURES"
    LIMITS = "LIMITS"
    PRICING = "PRICING"
    VERSIONS = "VERSIONS"
    LEGAL = "LEGAL"
    SUPPORT = "SUPPORT"


class ProfileReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    SUSPENDED = "SUSPENDED"


class NotificationChannel(StrEnum):
    PUSH = "PUSH"
    EMAIL = "EMAIL"
    SMS = "SMS"


class NotificationCampaignStatus(StrEnum):
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
