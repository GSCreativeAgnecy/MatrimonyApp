from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.enums import SwipeAction


class SwipeCreate(BaseModel):
    target_user_id: str
    action: SwipeAction


class SwipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_user_id: str
    to_user_id: str
    action: str
    created_at: datetime
    match_created: bool = False
    match_id: str | None = None


class MatchResponse(BaseModel):
    id: str
    user_id: str
    first_name: str | None = None
    age: int | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    occupation: str | None = None
    profile_photo: str | None = None
    status: str
    matched_at: datetime | None = None


class RecommendationItem(BaseModel):
    candidate_user_id: str
    score: float
    reason_codes: list[str]


class RecommendationFeed(BaseModel):
    items: list[RecommendationItem]
    next_cursor: str | None = None
    has_more: bool = False


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str | None = None
    body: str | None = None
    data: dict[str, Any] | None = None
    is_read: bool
    created_at: datetime


class ReportCreate(BaseModel):
    reported_user_id: str
    reason: str
    description: str | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reported_user_id: UUID
    reason: str
    status: str
    created_at: datetime
