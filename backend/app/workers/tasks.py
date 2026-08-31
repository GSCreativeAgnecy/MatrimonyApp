"""ARQ background jobs."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config.settings import settings
from app.db.enums import JobVerificationStatus, SubscriptionStatus
from app.db.models import JobVerification, ProfileShare, Subscription, User

logger = logging.getLogger("app.worker")


async def send_email(ctx: dict, to: str, subject: str, html: str) -> None:
    logger.info("Sending email to %s: %s", to, subject)
    if settings.SMTP_HOST and settings.SMTP_HOST != "localhost":
        # Real SMTP integration point; keep async-friendly via to_thread.
        pass
    return None


async def send_sms(ctx: dict, to: str, body: str) -> None:
    logger.info("Sending SMS to %s: %s", to, body)
    return None


async def send_push_notification(ctx: dict, user_id: str, title: str, body: str, data: dict | None = None) -> None:
    logger.info("Push to %s: %s", user_id, title)
    return None


async def process_photo_thumbnail(ctx: dict, photo_id: str) -> None:
    logger.info("Generating thumbnail for photo %s", photo_id)
    return None


async def process_payment_webhook(ctx: dict, provider: str, payload: dict) -> None:
    """Deferred idempotent webhook processing (retried by ARQ on failure)."""
    from app.services.payment_service import PaymentService

    engine = ctx["engine"]
    async with engine.connect():
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(engine) as session:
            await PaymentService(session).handle_webhook(provider, payload)
    return None


async def expire_subscriptions(ctx: dict) -> None:
    engine = ctx["engine"]
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        now = datetime.now(UTC)
        stmt = select(Subscription).where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at.is_not(None),
            Subscription.expires_at < now,
        )
        rows = (await session.execute(stmt)).scalars().all()
        for sub in rows:
            sub.status = SubscriptionStatus.EXPIRED
        await session.commit()
        logger.info("Expired %d subscriptions", len(rows))


async def expire_profile_shares(ctx: dict) -> None:
    engine = ctx["engine"]
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        now = datetime.now(UTC)
        stmt = select(ProfileShare).where(
            ProfileShare.revoked_at.is_(None),
            ProfileShare.expires_at.is_not(None),
            ProfileShare.expires_at < now,
        )
        rows = (await session.execute(stmt)).scalars().all()
        for share in rows:
            share.revoked_at = now
        await session.commit()
        logger.info("Expired %d profile shares", len(rows))


async def expire_job_verifications(ctx: dict) -> None:
    engine = ctx["engine"]
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        now = datetime.now(UTC)
        stmt = select(JobVerification).where(
            JobVerification.verification_status == JobVerificationStatus.VERIFIED,
            JobVerification.expires_at.is_not(None),
            JobVerification.expires_at < now,
        )
        rows = (await session.execute(stmt)).scalars().all()
        for v in rows:
            v.verification_status = JobVerificationStatus.EXPIRED
        await session.commit()
        logger.info("Expired %d job verifications", len(rows))


async def cleanup_deleted_accounts(ctx: dict, *, older_than_days: int = 30) -> None:
    """Anonymize accounts soft-deleted more than `older_than_days` ago."""
    engine = ctx["engine"]
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        stmt = select(User).where(User.deleted_at.is_not(None), User.deleted_at < cutoff)
        rows = (await session.execute(stmt)).scalars().all()
        for user in rows:
            user.phone_number = None
            user.email = None
            user.password_hash = None
        await session.commit()
        logger.info("Anonymized %d deleted accounts", len(rows))


async def process_notification_campaign(ctx: dict, campaign_id: str) -> dict:
    """Fan out a campaign in batches. Idempotent — a rerun after completion is a no-op."""
    from uuid import UUID

    from app.services.notification_campaign_service import NotificationCampaignService

    engine = ctx["engine"]
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        return await NotificationCampaignService(session).process(UUID(campaign_id))
