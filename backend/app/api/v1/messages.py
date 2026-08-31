from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.message import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.message_service import MessageService

router = APIRouter(tags=["messaging"])


@router.get("/conversations", summary="List my conversations", response_model=ApiResponse[list[ConversationResponse]])
async def list_conversations(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[ConversationResponse]]:
    service = MessageService(session)
    data = await service.list_conversations(user)
    return ApiResponse(data=[ConversationResponse(**d) for d in data])


@router.post(
    "/conversations", summary="Start a conversation with a match", response_model=ApiResponse[ConversationResponse]
)
async def start_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[ConversationResponse]:
    service = MessageService(session)
    data = await service.start_conversation(user, UUID(body.user_id))
    await session.commit()
    return ApiResponse(data=ConversationResponse(**data))


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="List messages",
    response_model=ApiResponse[list[MessageResponse]],
)
async def list_messages(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=200),
    before: UUID | None = Query(default=None),
) -> ApiResponse[list[MessageResponse]]:
    service = MessageService(session)
    messages = await service.messages(user, conversation_id, limit=limit, before=before)
    return ApiResponse(data=[MessageResponse.model_validate(m) for m in messages])


@router.post(
    "/conversations/{conversation_id}/messages", summary="Send a message", response_model=ApiResponse[MessageResponse]
)
async def send_message(
    conversation_id: UUID,
    body: MessageCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[MessageResponse]:
    service = MessageService(session)
    message = await service.send(user, conversation_id, body.model_dump())
    await session.commit()
    return ApiResponse(data=MessageResponse.model_validate(message))


@router.post(
    "/conversations/{conversation_id}/read", summary="Mark a conversation as read", response_model=ApiResponse[dict]
)
async def mark_read(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:
    service = MessageService(session)
    await service.mark_read(user, conversation_id)
    await session.commit()
    return ApiResponse(data={"status": "read"})
