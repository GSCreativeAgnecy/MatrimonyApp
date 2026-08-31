from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select

from app.db.enums import SubscriptionStatus
from app.db.models import Payment, Subscription, SubscriptionPlan, User
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    async def get_active(self, user_id: UUID) -> Subscription | None:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def is_premium(self, user_id: UUID) -> bool:
        sub = await self.get_active(user_id)
        if not sub or not sub.expires_at:
            return False
        return sub.expires_at > datetime.now(UTC)

    async def expire_due(self) -> list[Subscription]:
        now = datetime.now(UTC)
        stmt = select(Subscription).where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at.is_not(None),
            Subscription.expires_at < now,
        )
        return list((await self.session.execute(stmt)).scalars().all())


class SubscriptionPlanRepository(BaseRepository[SubscriptionPlan]):
    model = SubscriptionPlan

    async def list_active(self) -> list[SubscriptionPlan]:
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.price)
        return list((await self.session.execute(stmt)).scalars().all())


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def get_by_provider_id(self, provider: str, provider_payment_id: str) -> Payment | None:
        return await self.session.scalar(
            select(Payment).where(Payment.provider == provider, Payment.provider_payment_id == provider_payment_id)
        )

    # ---------- admin ----------

    async def admin_search(
        self,
        *,
        statuses: list[str] | None = None,
        payment_type: str | None = None,
        user_id: UUID | None = None,
        search: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        stmt = select(Payment, User.email).outerjoin(User, User.id == Payment.user_id)
        count_stmt = select(func.count()).select_from(Payment)
        conds: list[Any] = []
        if statuses:
            conds.append(Payment.status.in_(statuses))
        if payment_type:
            conds.append(Payment.payment_type == payment_type)
        if user_id is not None:
            conds.append(Payment.user_id == user_id)
        if search:
            like = f"%{search}%"
            conds.append(
                or_(User.email.ilike(like), User.phone_number.ilike(like), Payment.provider_payment_id.ilike(like))
            )
        if date_from is not None:
            conds.append(Payment.created_at >= date_from)
        if date_to is not None:
            conds.append(Payment.created_at < date_to)
        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (await self.session.execute(stmt.order_by(Payment.created_at.desc()).limit(limit).offset(offset))).all()
        return (
            [
                {
                    "id": str(p.id),
                    "user_id": str(p.user_id),
                    "user_name": user_email,
                    "amount": p.amount,
                    "currency": p.currency,
                    "payment_type": p.payment_type,
                    "status": p.status.value,
                    "provider": p.provider,
                    "provider_payment_id": p.provider_payment_id,
                    "created_at": p.created_at,
                    "paid_at": p.paid_at,
                }
                for p, user_email in rows
            ],
            total,
        )

    async def get_detail(self, payment_id: UUID) -> tuple[Payment | None, str | None]:
        row = (
            await self.session.execute(
                select(Payment, User.email).outerjoin(User, User.id == Payment.user_id).where(Payment.id == payment_id)
            )
        ).first()
        return (row[0], row[1]) if row else (None, None)


class SubscriptionAdminQueries(BaseRepository[Subscription]):
    model = Subscription

    async def admin_search(
        self,
        *,
        statuses: list[str] | None = None,
        user_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        stmt = (
            select(Subscription, User.email, SubscriptionPlan.name)
            .outerjoin(User, User.id == Subscription.user_id)
            .outerjoin(SubscriptionPlan, SubscriptionPlan.id == Subscription.plan_id)
        )
        count_stmt = select(func.count()).select_from(Subscription)
        conds: list[Any] = []
        if statuses:
            conds.append(Subscription.status.in_(statuses))
        if user_id is not None:
            conds.append(Subscription.user_id == user_id)
        if search:
            like = f"%{search}%"
            conds.append(or_(User.email.ilike(like), User.phone_number.ilike(like), SubscriptionPlan.name.ilike(like)))
        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (
            await self.session.execute(stmt.order_by(Subscription.created_at.desc()).limit(limit).offset(offset))
        ).all()
        return (
            [
                {
                    "id": str(s.id),
                    "user_id": str(s.user_id),
                    "user_name": user_email,
                    "plan_id": str(s.plan_id),
                    "plan_name": plan_name,
                    "status": s.status.value,
                    "starts_at": s.starts_at,
                    "expires_at": s.expires_at,
                    "auto_renew": s.auto_renew,
                    "provider": s.provider,
                    "created_at": s.created_at,
                }
                for s, user_email, plan_name in rows
            ],
            total,
        )
