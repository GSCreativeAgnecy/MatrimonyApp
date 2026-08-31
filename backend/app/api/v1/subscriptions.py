from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.monetization import (
    CheckoutRequest,
    CheckoutResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscription", tags=["subscriptions"])


@router.get(
    "/plans", summary="List active subscription plans", response_model=ApiResponse[list[SubscriptionPlanResponse]]
)
async def list_plans(
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[list[SubscriptionPlanResponse]]:
    service = SubscriptionService(session)
    plans = await service.list_plans()
    return ApiResponse(data=[SubscriptionPlanResponse.model_validate(p) for p in plans])


@router.get("", summary="Get my subscription and premium status", response_model=ApiResponse[SubscriptionResponse])
async def my_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[SubscriptionResponse]:
    service = SubscriptionService(session)
    sub = await service.current(user.id)
    is_premium = await service.is_premium(user.id)
    plan = None
    if sub:
        from app.services.subscription_service import SubscriptionService as SS

        plan = await SS(session).plans.get(sub.plan_id)
    return ApiResponse(
        data=SubscriptionResponse(
            id=str(sub.id) if sub else None,
            plan_name=plan.name if plan else None,
            status=sub.status.value if sub else "NONE",
            starts_at=sub.starts_at if sub else None,
            expires_at=sub.expires_at if sub else None,
            auto_renew=sub.auto_renew if sub else False,
            is_premium=is_premium,
        )
    )


@router.post("/checkout", summary="Create a checkout for a plan", response_model=ApiResponse[CheckoutResponse])
async def checkout(
    body: CheckoutRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[CheckoutResponse]:
    service = SubscriptionService(session)
    data = await service.checkout(user, body.plan_id)
    await session.commit()
    return ApiResponse(data=CheckoutResponse(**data))
