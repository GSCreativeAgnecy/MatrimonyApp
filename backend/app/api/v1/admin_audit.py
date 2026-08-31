from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_permission
from app.db.models import AuditLog, User
from app.schemas.admin import AuditRow
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/admin/audit-logs", tags=["admin", "audit"])

# Audit logs are read-only. There is intentionally no mutation endpoint.
can_read = require_permission("audit_logs.read")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("", summary="List audit logs (read-only)", response_model=ApiResponse[list[AuditRow]])
async def list_audit_logs(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    actor_user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[AuditRow]]:
    stmt = select(AuditLog, User.email).outerjoin(User, User.id == AuditLog.actor_user_id)
    count_stmt = select(func.count()).select_from(AuditLog)
    conds = []
    if actor_user_id is not None:
        conds.append(AuditLog.actor_user_id == actor_user_id)
    if action:
        conds.append(AuditLog.action == action)
    if entity_type:
        conds.append(AuditLog.entity_type == entity_type)
    if entity_id:
        conds.append(AuditLog.entity_id == entity_id)
    if user_id is not None:
        conds.append(
            or_(
                AuditLog.actor_user_id == user_id,
                or_(AuditLog.entity_type == "user", AuditLog.entity_id == str(user_id)),
            )
        )
    if q:
        conds.append(
            or_(
                AuditLog.action.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
                AuditLog.entity_type.ilike(f"%{q}%"),
                AuditLog.entity_id.ilike(f"%{q}%"),
            )
        )
    if date_from is not None:
        conds.append(AuditLog.created_at >= date_from)
    if date_to is not None:
        conds.append(AuditLog.created_at < date_to + timedelta(days=1))
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    total = int((await session.execute(count_stmt)).scalar_one())
    rows = (await session.execute(stmt.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset))).all()
    return ApiResponse(
        data=[
            AuditRow(
                id=str(log.id),
                action=log.action,
                actor_user_id=str(log.actor_user_id) if log.actor_user_id else None,
                actor_name=actor_email,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.meta,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log, actor_email in rows
        ],
        meta=_meta(total, limit, offset),
    )
