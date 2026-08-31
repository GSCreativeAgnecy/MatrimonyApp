"""Admin analytics & dashboard aggregates.

All queries aggregate in the database (or in bounded Python bucketing from
daily aggregates). The admin dashboard never downloads raw rows to compute
statistics. These endpoints must stay cheap: every list/aggregate is filtered,
paged, and backed by existing indexes.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import JobVerificationStatus, PaymentStatus, ReportStatus, SubscriptionStatus
from app.db.models import (
    AuditLog,
    JobVerification,
    Match,
    Message,
    Payment,
    Report,
    Subscription,
    Swipe,
    User,
)

logger = logging.getLogger("app.admin_analytics")

REPORT_OPEN_STATUSES = (ReportStatus.PENDING, ReportStatus.UNDER_REVIEW, ReportStatus.ESCALATED)


@dataclass(frozen=True)
class AnalyticsRange:
    start: datetime
    end: datetime
    granularity: str  # hour | day | week | month


def _now() -> datetime:
    return datetime.now(UTC)


def start_of_today() -> datetime:
    now = _now()
    return datetime.combine(now.date(), time.min, tzinfo=UTC)


def parse_range(range_spec: str | None, *, from_: str | None = None, to: str | None = None) -> AnalyticsRange:
    """Parse a friendly range spec into start/end/granularity.

    ``range`` values: ``today`` | ``7d`` | ``30d`` | ``90d`` | ``custom``.
    """
    now = _now()
    if range_spec == "today":
        return AnalyticsRange(start=start_of_today(), end=now, granularity="hour")
    if range_spec == "custom" and from_ and to:
        try:
            start = datetime.fromisoformat(from_.replace("Z", "+00:00"))
            end = datetime.fromisoformat(to.replace("Z", "+00:00"))
            if start.tzinfo is None:
                start = start.replace(tzinfo=UTC)
            if end.tzinfo is None:
                end = end.replace(tzinfo=UTC)
        except ValueError as exc:
            raise ValueError("Invalid custom date range") from exc
        return AnalyticsRange(start=start, end=end, granularity="day")
    days = {"7d": 7, "30d": 30, "90d": 90}.get(range_spec or "30d", 30)
    granularity = {"7d": "day", "30d": "week", "90d": "week"}.get(range_spec or "30d", "week")
    return AnalyticsRange(start=now - timedelta(days=days), end=now, granularity=granularity)


class AdminAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------- helpers ----------

    async def _count(self, model, *, column=None, start=None, end=None, extra=None) -> int:
        stmt = select(func.count()).select_from(model)
        if column is not None and start is not None:
            stmt = stmt.where(column >= start)
        if column is not None and end is not None:
            stmt = stmt.where(column < end)
        if extra is not None:
            stmt = stmt.where(extra)
        return int((await self.session.execute(stmt)).scalar_one())

    async def _daily_counts(self, model, column, *, start, end, extra=None) -> dict[str, int]:
        stmt = (
            select(func.date(column).label("d"), func.count())
            .where(column >= start, column < end)
            .group_by(func.date(column))
        )
        if extra is not None:
            stmt = stmt.where(extra)
        rows = (await self.session.execute(stmt)).all()
        return {str(row[0]): int(row[1]) for row in rows}

    async def _daily_sums(self, model, column, value_column, *, start, end, extra=None) -> dict[str, Decimal]:
        stmt = (
            select(func.date(column).label("d"), func.coalesce(func.sum(value_column), 0))
            .where(column >= start, column < end)
            .group_by(func.date(column))
        )
        if extra is not None:
            stmt = stmt.where(extra)
        rows = (await self.session.execute(stmt)).all()
        return {str(row[0]): Decimal(str(row[1])) for row in rows}

    def _bucket_key(self, day: datetime, granularity: str) -> str:
        if granularity == "hour":
            return day.strftime("%Y-%m-%d %H:00")
        if granularity == "week":
            iso = day.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        if granularity == "month":
            return day.strftime("%Y-%m")
        return day.strftime("%Y-%m-%d")

    def _fill_series(self, rng: AnalyticsRange, counts: dict[str, int]) -> list[dict]:
        """Bucket a per-day (or per-hour) count dict into the requested granularity."""
        buckets: dict[str, int] = {}
        day = rng.start
        if rng.granularity == "hour":
            while day < rng.end:
                buckets[day.strftime("%Y-%m-%d %H:00")] = 0
                day += timedelta(hours=1)
        else:
            end_day = (rng.end - timedelta(microseconds=1)).replace(tzinfo=UTC)
            while day <= end_day:
                buckets[self._bucket_key(day, rng.granularity)] = 0
                day += timedelta(days=1)
        for raw_day, value in counts.items():
            try:
                parsed = datetime.strptime(raw_day, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                continue
            key = self._bucket_key(parsed, rng.granularity)
            if key in buckets:
                buckets[key] += value
        return [{"bucket": k, "count": v} for k, v in sorted(buckets.items())]

    # ---------- dashboard summary ----------

    async def summary(self) -> dict:
        today = start_of_today()
        under_review = JobVerification.verification_status == JobVerificationStatus.UNDER_REVIEW
        return {
            "total_users": await self._count(User, extra=User.deleted_at.is_(None)),
            "new_users_today": await self._count(User, column=User.created_at, start=today),
            "active_users_today": await self._count(
                User, column=User.last_active_at, start=today, extra=User.deleted_at.is_(None)
            ),
            "new_matches_today": await self._count(Match, column=Match.created_at, start=today),
            "pending_verifications": await self._count(JobVerification, extra=under_review),
            "open_reports": await self._count(
                Report, extra=Report.status.in_([s.value for s in REPORT_OPEN_STATUSES])
            ),
            "today_revenue": await self._sum_revenue(today, _now()),
            "active_premium_subscriptions": await self._count(
                Subscription,
                extra=((Subscription.status == SubscriptionStatus.ACTIVE) & (Subscription.expires_at > _now())),
            ),
        }

    async def _sum_revenue(self, start: datetime, end: datetime) -> Decimal:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.SUCCESS, Payment.paid_at >= start, Payment.paid_at < end
        )
        return Decimal(str((await self.session.execute(stmt)).scalar_one()))

    async def action_center(self) -> list[dict]:
        under_review = JobVerification.verification_status == JobVerificationStatus.UNDER_REVIEW
        return [
            {
                "key": "pending_verifications",
                "label": "Pending Verifications",
                "count": await self._count(JobVerification, extra=under_review),
                "link": "/verifications",
            },
            {
                "key": "open_reports",
                "label": "Open Reports",
                "count": await self._count(Report, extra=Report.status.in_([s.value for s in REPORT_OPEN_STATUSES])),
                "link": "/reports",
            },
            {
                "key": "failed_payments",
                "label": "Failed Payments",
                "count": await self._count(Payment, extra=Payment.status == PaymentStatus.FAILED),
                "link": "/payments?status=FAILED",
            },
            {
                "key": "job_verification_queue",
                "label": "Job Verification Queue",
                "count": await self._count(JobVerification, extra=under_review),
                "link": "/job-verifications",
            },
        ]

    async def recent_activity(self, limit: int = 20) -> list[dict]:
        stmt = (
            select(AuditLog, User.email)
            .outerjoin(User, User.id == AuditLog.actor_user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(min(limit, 100))
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "id": str(log.id),
                "action": log.action,
                "actor_user_id": str(log.actor_user_id) if log.actor_user_id else None,
                "actor_name": actor_email,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.meta,
                "created_at": log.created_at,
            }
            for log, actor_email in rows
        ]

    # ---------- time series ----------

    async def user_growth(self, rng: AnalyticsRange) -> list[dict]:
        counts = await self._daily_counts(User, User.created_at, start=rng.start, end=rng.end)
        return self._fill_series(rng, counts)

    async def engagement(self, rng: AnalyticsRange) -> list[dict]:
        swipes = await self._daily_counts(Swipe, Swipe.created_at, start=rng.start, end=rng.end)
        likes = await self._daily_counts(
            Swipe,
            Swipe.created_at,
            start=rng.start,
            end=rng.end,
            extra=Swipe.action.in_(["LIKE", "SUPER_LIKE"]),
        )
        matches = await self._daily_counts(Match, Match.created_at, start=rng.start, end=rng.end)
        messages = await self._daily_counts(Message, Message.created_at, start=rng.start, end=rng.end)

        series: dict[str, dict] = {}
        for raw in self._fill_series(rng, {}):
            series[raw["bucket"]] = {"bucket": raw["bucket"], "swipes": 0, "likes": 0, "matches": 0, "messages": 0}
        for source, key in ((swipes, "swipes"), (likes, "likes"), (matches, "matches"), (messages, "messages")):
            for raw_day, value in source.items():
                try:
                    parsed = datetime.strptime(raw_day, "%Y-%m-%d").replace(tzinfo=UTC)
                except ValueError:
                    continue
                bucket = self._bucket_key(parsed, rng.granularity)
                if bucket in series:
                    series[bucket][key] = value
        return list(series.values())

    async def revenue(self, rng: AnalyticsRange) -> list[dict]:
        sums = await self._daily_sums(
            Payment,
            Payment.paid_at,
            Payment.amount,
            start=rng.start,
            end=rng.end,
            extra=Payment.status == PaymentStatus.SUCCESS,
        )
        base = self._fill_series(rng, {})
        series: dict[str, dict] = {b["bucket"]: {"bucket": b["bucket"], "revenue": Decimal("0")} for b in base}
        for raw_day, value in sums.items():
            try:
                parsed = datetime.strptime(raw_day, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                continue
            bucket = self._bucket_key(parsed, rng.granularity)
            if bucket in series:
                series[bucket]["revenue"] += value
        return [{"bucket": b["bucket"], "revenue": str(b["revenue"])} for b in series.values()]

    async def moderation(self, rng: AnalyticsRange) -> list[dict]:
        reports = await self._daily_counts(Report, Report.created_at, start=rng.start, end=rng.end)
        suspensions = await self._daily_counts(
            AuditLog, AuditLog.created_at, start=rng.start, end=rng.end, extra=AuditLog.action == "admin.suspend"
        )
        bans = await self._daily_counts(
            AuditLog, AuditLog.created_at, start=rng.start, end=rng.end, extra=AuditLog.action == "admin.ban"
        )
        under_review = JobVerification.verification_status == JobVerificationStatus.UNDER_REVIEW
        pending = await self._daily_counts(
            JobVerification,
            JobVerification.created_at,
            start=rng.start,
            end=rng.end,
            extra=under_review,
        )
        series: dict[str, dict] = {}
        for raw in self._fill_series(rng, {}):
            series[raw["bucket"]] = {
                "bucket": raw["bucket"],
                "reports": 0,
                "suspensions": 0,
                "bans": 0,
                "pending_verifications": 0,
            }
        for source, key in (
            (reports, "reports"),
            (suspensions, "suspensions"),
            (bans, "bans"),
            (pending, "pending_verifications"),
        ):
            for raw_day, value in source.items():
                try:
                    parsed = datetime.strptime(raw_day, "%Y-%m-%d").replace(tzinfo=UTC)
                except ValueError:
                    continue
                bucket = self._bucket_key(parsed, rng.granularity)
                if bucket in series:
                    series[bucket][key] = value
        return list(series.values())

    # ---------- analytics (extended) ----------

    async def analytics_users(self, rng: AnalyticsRange) -> dict:
        today = start_of_today()
        total = await self._count(User, extra=User.deleted_at.is_(None))
        new = await self._count(User, column=User.created_at, start=rng.start)
        active = await self._count(User, column=User.last_active_at, start=rng.start, extra=User.deleted_at.is_(None))
        dau = await self._count(User, column=User.last_active_at, start=today, extra=User.deleted_at.is_(None))
        wau = await self._count(
            User, column=User.last_active_at, start=_now() - timedelta(days=7), extra=User.deleted_at.is_(None)
        )
        mau = await self._count(
            User, column=User.last_active_at, start=_now() - timedelta(days=30), extra=User.deleted_at.is_(None)
        )
        retention = round((active / total * 100), 2) if total else 0.0
        return {
            "total_users": total,
            "new_users": new,
            "active_users": active,
            "retention": retention,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "series": await self.user_growth(rng),
        }

    async def analytics_engagement(self, rng: AnalyticsRange) -> dict:
        series = await self.engagement(rng)
        total = {k: sum(int(b[k]) for b in series) for k in ("swipes", "likes", "matches", "messages")}
        return {**total, "series": series}

    async def analytics_matching(self, rng: AnalyticsRange) -> dict:
        likes = await self._count(
            Swipe,
            column=Swipe.created_at,
            start=rng.start,
            end=rng.end,
            extra=Swipe.action.in_(["LIKE", "SUPER_LIKE"]),
        )
        matches = await self._count(Match, column=Match.created_at, start=rng.start, end=rng.end)
        conversations = await self._count(Message, column=Message.created_at, start=rng.start, end=rng.end)
        like_to_match = round(matches / likes * 100, 2) if likes else 0.0
        match_to_conversation = round(conversations / matches * 100, 2) if matches else 0.0
        return {
            "likes": likes,
            "matches": matches,
            "messages": conversations,
            "like_to_match_rate": like_to_match,
            "match_to_conversation_rate": match_to_conversation,
        }

    async def analytics_revenue(self, rng: AnalyticsRange) -> dict:
        from app.db.enums import PaymentType

        revenue = await self._sum_revenue(rng.start, rng.end)
        subscription_revenue = await self._sum_revenue_by_type(rng, PaymentType.SUBSCRIPTION.value)
        verification_revenue = await self._sum_revenue_by_type(rng, PaymentType.JOB_VERIFICATION.value)
        refunds = await self._sum_revenue_by_status(rng, PaymentStatus.REFUNDED)
        premium_users = await self._count(
            Subscription,
            extra=((Subscription.status == SubscriptionStatus.ACTIVE) & (Subscription.expires_at > _now())),
        )
        total_users = await self._count(User, extra=User.deleted_at.is_(None))
        conversion = round(premium_users / total_users * 100, 2) if total_users else 0.0
        return {
            "revenue": str(revenue),
            "premium_conversion_rate": conversion,
            "premium_users": premium_users,
            "subscription_revenue": str(subscription_revenue),
            "job_verification_revenue": str(verification_revenue),
            "refunds": str(refunds),
            "series": await self.revenue(rng),
        }

    async def _sum_revenue_by_type(self, rng: AnalyticsRange, payment_type: str) -> Decimal:
        from app.db.enums import PaymentType as PT

        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.SUCCESS,
            Payment.paid_at >= rng.start,
            Payment.paid_at < rng.end,
            Payment.payment_type == PT(payment_type),
        )
        return Decimal(str((await self.session.execute(stmt)).scalar_one()))

    async def _sum_revenue_by_status(self, rng: AnalyticsRange, status: PaymentStatus) -> Decimal:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == status, Payment.created_at >= rng.start, Payment.created_at < rng.end
        )
        return Decimal(str((await self.session.execute(stmt)).scalar_one()))

    async def analytics_moderation(self, rng: AnalyticsRange) -> dict:
        series = await self.moderation(rng)
        total_reports = sum(int(b["reports"]) for b in series)
        total_bans = sum(int(b["bans"]) for b in series)
        total_suspensions = sum(int(b["suspensions"]) for b in series)
        under_review = JobVerification.verification_status == JobVerificationStatus.UNDER_REVIEW
        queue = await self._count(JobVerification, extra=under_review)
        return {
            "reports": total_reports,
            "bans": total_bans,
            "suspensions": total_suspensions,
            "verification_queue": queue,
            "series": series,
        }
