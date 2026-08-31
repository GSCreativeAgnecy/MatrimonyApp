from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_request_context, get_session, require_permission
from app.db.models import SubscriptionPlan, User
from app.repositories.billing_repo import SubscriptionAdminQueries
from app.schemas.admin import (
    AdminActionResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanRow,
    SubscriptionPlanUpdate,
    SubscriptionRow,
)
from app.schemas.common import ApiResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["admin", "subscriptions"])

can_read = require_permission("subscriptions.read")
can_manage = require_permission("subscriptions.manage")


def _meta(total: int, limit: int, offset: int) -> dict[str, Any]:
    return {"total": total, "limit": limit, "offset": offset, "count": min(total - offset, limit)}


@router.get("/subscriptions", summary="List subscriptions (admin)", response_model=ApiResponse[list[SubscriptionRow]])
async def list_subscriptions(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    user_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[SubscriptionRow]]:
    statuses = status.split(",") if status else None
    rows, total = await SubscriptionAdminQueries(session).admin_search(
        statuses=statuses, user_id=user_id, search=search, limit=limit, offset=offset
    )
    return ApiResponse(data=[SubscriptionRow(**r) for r in rows], meta=_meta(total, limit, offset))


@router.get(
    "/subscription-plans", summary="List subscription plans", response_model=ApiResponse[list[SubscriptionPlanRow]]
)
async def list_plans(
    admin: User = Depends(can_read),
    session: AsyncSession = Depends(get_session),
    include_inactive: bool = Query(default=True),
) -> ApiResponse[list[SubscriptionPlanRow]]:
    stmt = select(SubscriptionPlan).order_by(SubscriptionPlan.price)
    if not include_inactive:
        stmt = stmt.where(SubscriptionPlan.is_active.is_(True))
    rows = list((await session.execute(stmt)).scalars().all())
    return ApiResponse(data=[SubscriptionPlanRow.model_validate(r) for r in rows])


@router.post(
    "/subscription-plans", summary="Create a subscription plan", response_model=ApiResponse[SubscriptionPlanRow]
)
async def create_plan(
    payload: SubscriptionPlanCreate,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[SubscriptionPlanRow]:
    ctx = await get_request_context(request)
    plan = SubscriptionPlan(**payload.model_dump())
    session.add(plan)
    await session.flush()
    await AuditService(session).record(
        action="subscription_plan.created",
        actor_user_id=admin.id,
        entity_type="subscription_plan",
        entity_id=str(plan.id),
        metadata={"name": plan.name, "price": str(plan.price)},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=SubscriptionPlanRow.model_validate(plan))


@router.patch(
    "/subscription-plans/{plan_id}",
    summary="Update a subscription plan",
    response_model=ApiResponse[SubscriptionPlanRow],
)
async def update_plan(
    plan_id: UUID,
    payload: SubscriptionPlanUpdate,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[SubscriptionPlanRow]:
    ctx = await get_request_context(request)
    plan = await session.get(SubscriptionPlan, plan_id)
    if plan is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Plan not found", code="PLAN_NOT_FOUND")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    await AuditService(session).record(
        action="subscription_plan.updated",
        actor_user_id=admin.id,
        entity_type="subscription_plan",
        entity_id=str(plan.id),
        metadata={"changes": payload.model_dump(exclude_unset=True)},
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=SubscriptionPlanRow.model_validate(plan))


@router.post(
    "/subscription-plans/{plan_id}/deactivate",
    summary="Deactivate a subscription plan",
    response_model=ApiResponse[AdminActionResponse],
)
async def deactivate_plan(
    plan_id: UUID,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    plan = await session.get(SubscriptionPlan, plan_id)
    if plan is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Plan not found", code="PLAN_NOT_FOUND")
    plan.is_active = False
    await AuditService(session).record(
        action="subscription_plan.deactivated",
        actor_user_id=admin.id,
        entity_type="subscription_plan",
        entity_id=str(plan.id),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="deactivated", message="Plan deactivated"))


@router.post(
    "/subscription-plans/{plan_id}/activate",
    summary="Activate a subscription plan",
    response_model=ApiResponse[AdminActionResponse],
)
async def activate_plan(
    plan_id: UUID,
    request: Request,
    admin: User = Depends(can_manage),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[AdminActionResponse]:
    ctx = await get_request_context(request)
    plan = await session.get(SubscriptionPlan, plan_id)
    if plan is None:
        from app.api.errors import NotFoundError

        raise NotFoundError("Plan not found", code="PLAN_NOT_FOUND")
    plan.is_active = True
    await AuditService(session).record(
        action="subscription_plan.activated",
        actor_user_id=admin.id,
        entity_type="subscription_plan",
        entity_id=str(plan.id),
        ip_address=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    await session.commit()
    return ApiResponse(data=AdminActionResponse(status="activated", message="Plan activated"))
