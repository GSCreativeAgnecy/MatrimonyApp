from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.db.models import User
from app.repositories.match_repo import MatchRepository
from app.schemas.admin import MatchRow
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/admin/matches", tags=["admin", "matches"])

can_read = require_permission("users.read", "reports.read")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("", summary="List matches (admin)", response_model=ApiResponse[list[MatchRow]])
async def list_matches(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    user_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[MatchRow]]:
    rows, total = await MatchRepository(session).admin_search(
        user_id=user_id,
        search=search,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[MatchRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.get("/{match_id}", summary="Match detail (admin)", response_model=ApiResponse[dict])
async def match_detail(
    match_id: UUID,
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[dict]:

    from app.db.models import Match

    match = await session.get(Match, match_id)
    if match is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Match not found", code="MATCH_NOT_FOUND")
    return ApiResponse(
        data={
            "id": str(match.id),
            "user1_id": str(match.user1_id),
            "user2_id": str(match.user2_id),
            "status": match.status.value,
            "matched_at": match.matched_at,
            "unmatched_at": match.unmatched_at,
            "created_at": match.created_at,
        }
    )
