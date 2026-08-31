from datetime import UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ForbiddenError, NotFoundError
from app.db.models import ConversationParticipant, Message, User
from app.repositories.match_repo import MatchRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.moderation_repo import BlockRepository
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class MessageService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MessageRepository(session)
        self.matches = MatchRepository(session)
        self.users = UserRepository(session)
        self.blocks = BlockRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    async def _assert_participant(self, conversation_id: UUID, user_id: UUID):
        conversation = await self.repo.get_conversation_with_participant(conversation_id, user_id)
        if conversation is None:
            raise NotFoundError("Conversation not found", code="CONVERSATION_NOT_FOUND")
        return conversation

    async def list_conversations(self, user: User) -> list[dict]:
        conversations = await self.repo.conversations_for(user.id)
        result = []
        for conv in conversations:
            other_id = await self._other_participant(conv.id, user.id)
            other_profile = await self.users.ensure_profile(other_id)
            unread = await self.repo.unread_count(conv.id, user.id)
            last = await self._last_message(conv.id)
            result.append(
                {
                    "id": str(conv.id),
                    "other_user_id": str(other_id),
                    "other_user_name": other_profile.first_name,
                    "last_message_preview": last.body if last else None,
                    "last_message_at": last.created_at if last else conv.last_message_at,
                    "unread_count": unread,
                }
            )
        return result

    async def _other_participant(self, conversation_id: UUID, me: UUID) -> UUID:
        stmt = select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id != me,
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        if not rows:
            raise ForbiddenError("Conversation not accessible", code="FORBIDDEN")
        return rows[0]

    async def _last_message(self, conversation_id: UUID) -> Message | None:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def start_conversation(self, user: User, target_user_id: UUID) -> dict:
        target = await self.users.get(target_user_id)
        if not target:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")

        # Only matched users can message (per messaging policy).
        match = await self.matches.get_active_between(user.id, target_user_id)
        if match is None:
            raise ForbiddenError("You can only message your matches", code="NOT_MATCHED")
        if await self.blocks.get_pair(user.id, target_user_id) or await self.blocks.get_pair(target_user_id, user.id):
            raise ForbiddenError("You cannot message this user", code="BLOCKED")

        conv = await self.repo.get_direct_conversation(user.id, target_user_id)
        if conv is None:
            conv = await self.repo.create_conversation(user.id, target_user_id)
        return {"id": str(conv.id), "other_user_id": str(target_user_id)}

    async def messages(
        self, user: User, conversation_id: UUID, *, limit: int = 50, before: UUID | None = None
    ) -> list[Message]:
        await self._assert_participant(conversation_id, user.id)
        return await self.repo.messages_for(conversation_id, before=before, limit=limit)

    async def send(self, user: User, conversation_id: UUID, data: dict) -> Message:
        await self._assert_participant(conversation_id, user.id)
        message = await self.repo.create(
            conversation_id=conversation_id,
            sender_id=user.id,
            message_type=data.get("message_type", "TEXT"),
            body=data.get("body"),
            media_url=data.get("media_url"),
        )
        conv = await self.repo.get_conversation(conversation_id)
        if conv:
            from datetime import datetime

            conv.last_message_at = datetime.now(UTC)
        other_id = await self._other_participant(conversation_id, user.id)
        await self.notifications.create(
            other_id, type="NEW_MESSAGE", title="New message", body=data.get("body") or "New message"
        )
        return message

    async def mark_read(self, user: User, conversation_id: UUID) -> None:
        await self._assert_participant(conversation_id, user.id)
        await self.repo.mark_conversation_read(conversation_id, user.id)
