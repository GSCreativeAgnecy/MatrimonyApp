from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    GUID,
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UTCDateTime,
    enum_column,
    gen_uuid,
)
from app.db.enums import MessageType


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    last_message_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True, index=True)

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_conversation_user"),)

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(UTCDateTime, default=datetime.utcnow, nullable=False)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="participants")


class Message(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    message_type: Mapped[MessageType] = enum_column(MessageType, default=MessageType.TEXT)
    body: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)
