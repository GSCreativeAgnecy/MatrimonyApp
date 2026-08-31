from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.enums import EmploymentType


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    price: float
    currency: str
    duration_days: int
    features: dict | None = None


class SubscriptionResponse(BaseModel):
    id: UUID | None = None
    plan_name: str | None = None
    status: str
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    auto_renew: bool
    is_premium: bool = False


class CheckoutRequest(BaseModel):
    plan_id: str


class CheckoutResponse(BaseModel):
    checkout_url: str | None = None
    payment_id: str
    provider: str
    amount: float
    currency: str


class JobVerificationCreate(BaseModel):
    employment_type: EmploymentType
    employer_name: str
    job_title: str | None = None
    country: str | None = None


class JobVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
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
    rejection_reason: str | None = None


class JobVerificationCheckoutResponse(BaseModel):
    verification_id: str
    checkout_url: str | None = None
    payment_id: str
    amount: float
    currency: str


class ProfileShareCreate(BaseModel):
    shared_with_user_id: str
    permission: str = "VIEW"
    expires_in_days: int | None = None


class ProfileShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shared_with_user_id: UUID
    permission: str
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime
