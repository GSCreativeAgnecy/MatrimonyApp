from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_context, get_session, require_permission
from app.db.models import ConversationParticipant, User
from app.repositories.message_repo import MessageRepository
from app.schemas.admin import ConversationRow, MessageRow
from app.schemas.common import ApiResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin/messages", tags=["admin", "messages"])

# Reading private conversations is a high-privilege, audited action.
can_read_private = require_permission("messages.read_private")
can_read_users = require_permission("users.read")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get(
    "/conversations", summary="Search conversations (admin)", response_model=ApiResponse[list[ConversationRow]]
)
async def search_conversations(
    admin: User = Depends(can_read_users),
    session: AsyncSession = Depends(get_session),
    user_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[ConversationRow]]:
    rows, total = await MessageRepository(session).admin_conversations(
        user_id=user_id, search=search, limit=limit, offset=offset
    )
    return ApiResponse(data=[ConversationRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.get(
    "/conversations/{conversation_id}", summary="View a conversation (audited)", response_model=ApiResponse[dict]
)
async def conversation_detail(
    conversation_id: UUID,
    request: Request,
    admin: User = Depends(can_read_private),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=200, ge=1, le=500),
    before: UUID | None = Query(default=None),
) -> ApiResponse[dict]:
    repo = MessageRepository(session)
    conversation = await repo.get_conversation(conversation_id)
    if conversation is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Conversation not found", code="CONVERSATION_NOT_FOUND")

    ctx = await get_request_context(request)
    # Every private-message access is recorded: admin identity + conversation id.
    await AuditService(session).record(
        action="admin.message_view",
        actor_user_id=admin.id,
        entity_type="conversation",
        entity_id=str(conversation.id),
        metadata={"access": "private_conversation"},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()

    participants = (
        (
            await session.execute(
                select(ConversationParticipant.user_id).where(
                    ConversationParticipant.conversation_id == conversation.id
                )
            )
        )
        .scalars()
        .all()
    )
    messages = await repo.admin_messages(conversation.id, before=before, limit=limit)
    return ApiResponse(
        data={
            "id": str(conversation.id),
            "participant_ids": [str(p) for p in participants],
            "last_message_at": conversation.last_message_at,
            "created_at": conversation.created_at,
            "audited": True,
            "messages": [
                MessageRow(
                    id=str(m.id),
                    conversation_id=str(m.conversation_id),
                    sender_id=str(m.sender_id),
                    message_type=m.message_type,
                    body=m.body,
                    media_url=m.media_url,
                    created_at=m.created_at,
                    read_at=m.read_at,
                ).model_dump()
                for m in messages
            ],
        }
    )
