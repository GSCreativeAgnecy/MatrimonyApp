from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import MessageType


class ConversationCreate(BaseModel):
    user_id: str


class ConversationResponse(BaseModel):
    id: str
    other_user_id: str
    other_user_name: str | None = None
    other_user_photo: str | None = None
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0


class MessageCreate(BaseModel):
    message_type: MessageType = MessageType.TEXT
    body: str | None = Field(default=None, max_length=5000)
    media_url: str | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID
    message_type: str
    body: str | None = None
    media_url: str | None = None
    created_at: datetime
    read_at: datetime | None = None
