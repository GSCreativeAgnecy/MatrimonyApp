from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import NotFoundError
from app.db.enums import PaymentType, SubscriptionStatus
from app.db.models import Payment, Subscription, SubscriptionPlan, User
from app.repositories.billing_repo import SubscriptionPlanRepository, SubscriptionRepository
from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService


class SubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SubscriptionRepository(session)
        self.plans = SubscriptionPlanRepository(session)
        self.audit = AuditService(session)

    async def list_plans(self) -> list[SubscriptionPlan]:
        return await self.plans.list_active()

    async def get_plan(self, plan_id) -> SubscriptionPlan:
        plan = await self.plans.get(plan_id)
        if plan is None or not plan.is_active:
            raise NotFoundError("Plan not found", code="PLAN_NOT_FOUND")
        return plan

    async def current(self, user_id) -> Subscription | None:
        return await self.repo.get_active(user_id)

    async def is_premium(self, user_id) -> bool:
        return await self.repo.is_premium(user_id)

    async def checkout(self, user: User, plan_id) -> dict:
        plan = await self.get_plan(plan_id)
        payments = PaymentService(self.session)
        return await payments.create_checkout(
            user,
            payment_type=PaymentType.SUBSCRIPTION,
            amount=Decimal(str(plan.price)),
            currency=plan.currency,
            metadata={
                "plan_id": str(plan.id),
                "description": plan.name,
                "duration_days": plan.duration_days,
            },
        )

    async def activate_from_payment(self, payment: Payment) -> Subscription:
        """Create/renew the user's subscription from a verified successful payment."""
        meta = payment.meta or {}
        plan_id = meta.get("plan_id")
        if not plan_id:
            raise NotFoundError("Missing plan metadata on payment", code="PAYMENT_META_MISSING")
        plan = await self.plans.get(plan_id)
        if plan is None:
            raise NotFoundError("Plan not found", code="PLAN_NOT_FOUND")

        now = datetime.now(UTC)
        existing = await self.repo.get_active(payment.user_id)
        starts_at = existing.expires_at if existing and existing.expires_at and existing.expires_at > now else now
        expires_at = starts_at + timedelta(days=plan.duration_days)

        if existing:
            existing.starts_at = starts_at
            existing.expires_at = expires_at
            existing.status = SubscriptionStatus.ACTIVE
            existing.provider = payment.provider
            existing.provider_subscription_id = payment.provider_payment_id
            subscription = existing
        else:
            subscription = await self.repo.create(
                user_id=payment.user_id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
                starts_at=starts_at,
                expires_at=expires_at,
                auto_renew=False,
                provider=payment.provider,
                provider_subscription_id=payment.provider_payment_id,
            )
        await self.audit.record(
            action="subscription.change",
            actor_user_id=payment.user_id,
            entity_type="subscription",
            entity_id=str(subscription.id),
        )
        return subscription

    async def expire_due(self) -> list[Subscription]:
        return await self.repo.expire_due()
