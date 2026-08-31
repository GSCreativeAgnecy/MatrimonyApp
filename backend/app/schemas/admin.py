from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# NOTE: numeric fields use ``float`` (not Decimal) so ORJSON/JSON responses
# serialize cleanly. The database still stores exact Numeric columns.


# ---------- dashboard / analytics ----------


class DashboardSummary(BaseModel):
    total_users: int
    new_users_today: int
    active_users_today: int
    new_matches_today: int
    pending_verifications: int
    open_reports: int
    today_revenue: float
    active_premium_subscriptions: int


class TimeBucket(BaseModel):
    bucket: str
    count: int = 0


class EngagementBucket(BaseModel):
    bucket: str
    swipes: int = 0
    likes: int = 0
    matches: int = 0
    messages: int = 0


class RevenueBucket(BaseModel):
    bucket: str
    revenue: float = 0.0


class ModerationBucket(BaseModel):
    bucket: str
    reports: int = 0
    suspensions: int = 0
    bans: int = 0
    pending_verifications: int = 0


class ActionCenterItem(BaseModel):
    key: str
    label: str
    count: int
    link: str


class RecentActivityItem(BaseModel):
    id: str
    action: str
    actor_user_id: str | None = None
    actor_name: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime | None = None


# ---------- users ----------


class AdminUserListRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    gender: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    religion: str | None = None
    caste: str | None = None
    education: str | None = None
    occupation: str | None = None
    role: str | None = None
    account_status: str | None = None
    is_banned: bool = False
    is_premium: bool = False
    verified: bool = False
    profile_photo: str | None = None
    last_active_at: datetime | None = None
    created_at: datetime | None = None


class AdminUserDetail(BaseModel):
    id: str
    email: str | None = None
    phone_number: str | None = None
    account_status: str
    role: str
    is_banned: bool
    banned_at: datetime | None = None
    suspended_at: datetime | None = None
    suspended_until: datetime | None = None
    suspended_reason: str | None = None
    email_verified: bool = False
    phone_verified: bool = False
    last_login_at: datetime | None = None
    last_active_at: datetime | None = None
    created_at: datetime | None = None
    profile: dict[str, Any] | None = None
    is_premium: bool = False
    subscription: dict[str, Any] | None = None


class AdminActionResponse(BaseModel):
    status: str
    message: str = ""


class SuspendRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)
    duration_minutes: int | None = Field(default=None, gt=0, le=525600)
    admin_notes: str | None = Field(default=None, max_length=1000)


class BanRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)
    admin_notes: str | None = Field(default=None, max_length=1000)


class DeleteUserRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)
    admin_notes: str | None = Field(default=None, max_length=1000)


class VerifyUserRequest(BaseModel):
    kind: str = Field(pattern="^(email|phone)$")


class RoleChangeRequest(BaseModel):
    role: str = Field(pattern="^(USER|MODERATOR|VERIFIER|SUPPORT|FINANCE|ANALYST|ADMIN|SUPER_ADMIN)$")


# ---------- reports / moderation ----------


class ReportRow(BaseModel):
    id: str
    reporter_id: str
    reported_user_id: str
    reporter_name: str | None = None
    reported_name: str | None = None
    reason: str
    description: str | None = None
    status: str
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None


class ReportDetail(ReportRow):
    reporter_email: str | None = None
    reported_email: str | None = None
    evidence: dict[str, Any] | None = None
    history: list[dict[str, Any]] = []


# ---------- photos ----------


class PhotoRow(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    url: str | None = None
    thumbnail_url: str | None = None
    verification_status: str
    mime_type: str | None = None
    is_profile_photo: bool = False
    uploaded_at: datetime | None = None
    created_at: datetime | None = None


# ---------- job verification ----------


class JobVerificationRow(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    employment_type: str
    employer_name: str
    job_title: str | None = None
    country: str | None = None
    verification_status: str
    amount_paid: float | None = None
    currency: str | None = None
    submitted_at: datetime | None = None
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    reviewer_notes: str | None = None
    rejection_reason: str | None = None
    created_at: datetime | None = None


# ---------- matches ----------


class MatchRow(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    user1_name: str | None = None
    user2_name: str | None = None
    status: str
    matched_at: datetime | None = None
    unmatched_at: datetime | None = None
    created_at: datetime | None = None


# ---------- messages ----------


class ConversationRow(BaseModel):
    id: str
    participant_ids: list[str]
    participants: list[dict[str, Any]] = []
    last_message_at: datetime | None = None
    message_count: int = 0
    created_at: datetime | None = None


class MessageRow(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    message_type: str
    body: str | None = None
    media_url: str | None = None
    created_at: datetime | None = None
    read_at: datetime | None = None


# ---------- payments ----------


class PaymentRow(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    amount: float
    currency: str
    payment_type: str
    status: str
    provider: str
    provider_payment_id: str | None = None
    created_at: datetime | None = None
    paid_at: datetime | None = None


class PaymentDetail(PaymentRow):
    meta: dict[str, Any] | None = None


# ---------- subscriptions ----------


class SubscriptionRow(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    plan_id: str | None = None
    plan_name: str | None = None
    status: str
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    auto_renew: bool = False
    provider: str | None = None
    created_at: datetime | None = None


class SubscriptionPlanRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    name: str
    description: str | None = None
    price: float
    currency: str
    duration_days: int
    features: dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime | None = None


class SubscriptionPlanCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    duration_days: int = Field(gt=0)
    features: dict[str, Any] = {}


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    duration_days: int | None = Field(default=None, gt=0)
    features: dict[str, Any] | None = None
    is_active: bool | None = None


# ---------- notifications ----------


class CampaignAudience(BaseModel):
    type: str = Field(pattern="^(all|premium|unverified|city|country|custom)$")
    city: str | None = None
    country: str | None = None
    user_ids: list[str] | None = None


class CampaignCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    message: str = Field(min_length=2, max_length=2000)
    channel: str = Field(default="PUSH", pattern="^(PUSH|EMAIL|SMS)$")
    audience: CampaignAudience
    schedule_at: datetime | None = None


class CampaignRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Any
    title: str
    message: str
    channel: str
    audience: dict[str, Any]
    status: str
    target_count: int | None = None
    delivered_count: int = 0
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: Any = None
    created_at: datetime | None = None


# ---------- audit ----------


class AuditRow(BaseModel):
    id: str
    action: str
    actor_user_id: str | None = None
    actor_name: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime | None = None


# ---------- admin users / roles ----------


class AdminUserRow(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None
    role: str
    account_status: str
    is_banned: bool = False
    two_factor_enabled: bool = False
    last_login_at: datetime | None = None
    created_at: datetime | None = None


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str = Field(pattern="^(MODERATOR|VERIFIER|SUPPORT|FINANCE|ANALYST|ADMIN|SUPER_ADMIN)$")
    name: str | None = Field(default=None, max_length=200)


class RolePermissionsResponse(BaseModel):
    role: str
    permissions: list[str]


class RolePermissionsUpdate(BaseModel):
    permissions: list[str] = []
