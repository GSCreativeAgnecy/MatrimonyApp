from datetime import UTC
from uuid import UUID

from sqlalchemy import func, or_, select

from app.db.models import Conversation, ConversationParticipant, Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        return await self.session.get(Conversation, conversation_id)

    async def get_conversation_with_participant(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        stmt = (
            select(Conversation)
            .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
            .where(Conversation.id == conversation_id, ConversationParticipant.user_id == user_id)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def get_direct_conversation(self, a: UUID, b: UUID) -> Conversation | None:
        conv_ids_a = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == a)
            .scalar_subquery()
        )
        stmt = (
            select(ConversationParticipant.conversation_id)
            .where(
                ConversationParticipant.user_id == b,
                ConversationParticipant.conversation_id.in_(conv_ids_a),
            )
            .limit(1)
        )
        conv_id = (await self.session.execute(stmt)).scalar_one_or_none()
        return await self.session.get(Conversation, conv_id) if conv_id else None

    async def create_conversation(self, a: UUID, b: UUID) -> Conversation:
        conv = Conversation()
        self.session.add(conv)
        await self.session.flush()
        self.session.add_all(
            [
                ConversationParticipant(conversation_id=conv.id, user_id=a),
                ConversationParticipant(conversation_id=conv.id, user_id=b),
            ]
        )
        await self.session.flush()
        return conv

    async def conversations_for(self, user_id: UUID) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
            .where(ConversationParticipant.user_id == user_id)
            .order_by(Conversation.last_message_at.desc().nullslast())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def messages_for(
        self, conversation_id: UUID, *, before: UUID | None = None, limit: int = 50
    ) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
        if before:
            stmt = stmt.where(Message.id < before)
        stmt = stmt.order_by(Message.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def unread_count(self, conversation_id: UUID, user_id: UUID) -> int:
        stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.read_at.is_(None),
            Message.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one() or 0

    async def mark_conversation_read(self, conversation_id: UUID, user_id: UUID) -> None:
        from datetime import datetime

        stmt = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sender_id != user_id,
                Message.read_at.is_(None),
            )
            .limit(500)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        now = datetime.now(UTC)
        for m in rows:
            m.read_at = now

    # ---------- admin ----------

    async def admin_conversations(
        self,
        *,
        user_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        from app.db.models import User

        count_stmt = select(func.count()).select_from(Conversation)
        base_conds = []
        if user_id is not None:
            exists_participant = select(ConversationParticipant.conversation_id).where(
                ConversationParticipant.user_id == user_id
            )
            base_conds.append(Conversation.id.in_(exists_participant))
        if search:
            like = f"%{search}%"
            matching_users = select(User.id).where(or_(User.email.ilike(like), User.phone_number.ilike(like)))
            exists_participant = select(ConversationParticipant.conversation_id).where(
                ConversationParticipant.user_id.in_(matching_users)
            )
            base_conds.append(Conversation.id.in_(exists_participant))
        for c in base_conds:
            count_stmt = count_stmt.where(c)
        total = int((await self.session.execute(count_stmt)).scalar_one())

        convs = list(
            (
                await self.session.execute(
                    select(Conversation)
                    .where(*base_conds)
                    .order_by(Conversation.last_message_at.desc().nullslast())
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        result = []
        for conv in convs:
            participants = (
                await self.session.execute(
                    select(ConversationParticipant, User.email, User.phone_number)
                    .outerjoin(User, User.id == ConversationParticipant.user_id)
                    .where(ConversationParticipant.conversation_id == conv.id)
                )
            ).all()
            message_count = await self.session.scalar(
                select(func.count(Message.id)).where(Message.conversation_id == conv.id, Message.deleted_at.is_(None))
            )
            result.append(
                {
                    "id": str(conv.id),
                    "participant_ids": [str(p.user_id) for p, _, _ in participants],
                    "participants": [
                        {
                            "user_id": str(p.user_id),
                            "email": email,
                            "phone_number": phone,
                        }
                        for p, email, phone in participants
                    ],
                    "last_message_at": conv.last_message_at,
                    "message_count": int(message_count or 0),
                    "created_at": conv.created_at,
                }
            )
        return result, total

    async def admin_messages(
        self, conversation_id: UUID, *, before: UUID | None = None, limit: int = 200
    ) -> list[Message]:
        return await self.messages_for(conversation_id, before=before, limit=limit)
