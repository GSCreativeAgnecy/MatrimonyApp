"""Admin notification campaigns.

The campaign is persisted and the actual fan-out runs in the ``process_notification_campaign``
ARQ worker — never synchronously inside the HTTP request. Audience resolution and
creation are batched to keep memory bounded. All campaigns are audited.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ValidationAppError
from app.db.enums import NotificationCampaignStatus, NotificationType, SubscriptionStatus
from app.db.models import Notification, NotificationCampaign, Profile, Subscription, User
from app.services.audit_service import AuditService

MAX_CAMPAIGN_AUDIENCE = 100_000
CAMPAIGN_BATCH_SIZE = 1000


class NotificationCampaignService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def create(self, admin: User, data: dict) -> NotificationCampaign:
        audience = data["audience"]
        audience_type = audience["type"]
        if audience_type not in {"all", "premium", "unverified", "city", "country", "custom"}:
            raise ValidationAppError("Invalid audience type", code="INVALID_AUDIENCE")

        target_ids, count = await self._resolve_audience(audience)
        if count > MAX_CAMPAIGN_AUDIENCE:
            raise ValidationAppError(
                f"Audience of {count} exceeds the {MAX_CAMPAIGN_AUDIENCE} campaign limit",
                code="AUDIENCE_LIMIT_EXCEEDED",
            )
        if count == 0:
            raise ValidationAppError("Audience is empty", code="EMPTY_AUDIENCE")

        campaign = NotificationCampaign(
            title=data["title"],
            message=data["message"],
            channel=data["channel"],
            audience=audience,
            status=NotificationCampaignStatus.QUEUED,
            target_count=count,
            scheduled_at=data.get("schedule_at"),
            created_by=admin.id,
        )
        self.session.add(campaign)
        await self.session.flush()

        await self.audit.record(
            action="notification_campaign.created",
            actor_user_id=admin.id,
            entity_type="notification_campaign",
            entity_id=str(campaign.id),
            metadata={
                "title": data["title"],
                "channel": data["channel"],
                "audience_type": audience_type,
                "target_count": count,
                "scheduled_at": data.get("schedule_at"),
            },
        )
        return campaign

    async def _resolve_audience(self, audience: dict) -> tuple[list[UUID], int]:
        a_type = audience["type"]
        if a_type == "custom":
            user_ids = [UUID(uid) for uid in (audience.get("user_ids") or [])]
            if not user_ids:
                raise ValidationAppError("Custom audience needs user_ids", code="INVALID_AUDIENCE")
            stmt = select(User.id).where(User.id.in_(user_ids), User.deleted_at.is_(None))
        elif a_type == "premium":
            stmt = (
                select(User.id)
                .join(Subscription, Subscription.user_id == User.id)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.expires_at > datetime.now(UTC),
                    User.deleted_at.is_(None),
                )
            )
        elif a_type == "unverified":
            stmt = select(User.id).where(
                User.deleted_at.is_(None),
                User.email_verified_at.is_(None),
                User.phone_verified_at.is_(None),
            )
        elif a_type == "city":
            city = audience.get("city")
            if not city:
                raise ValidationAppError("City audience needs a city", code="INVALID_AUDIENCE")
            stmt = (
                select(User.id)
                .join(Profile, Profile.user_id == User.id)
                .where(Profile.city == city, User.deleted_at.is_(None))
            )
        elif a_type == "country":
            country = audience.get("country")
            if not country:
                raise ValidationAppError("Country audience needs a country", code="INVALID_AUDIENCE")
            stmt = (
                select(User.id)
                .join(Profile, Profile.user_id == User.id)
                .where(Profile.country == country, User.deleted_at.is_(None))
            )
        else:  # all
            stmt = select(User.id).where(User.deleted_at.is_(None))

        ids = list((await self.session.execute(stmt)).scalars().all())
        return ids, len(ids)

    # ---------- worker-side ----------

    async def process(self, campaign_id: UUID) -> dict:
        """Resolve the audience and create notifications in batches."""
        campaign = await self.session.get(NotificationCampaign, campaign_id)
        if campaign is None:
            return {"status": "missing"}
        if campaign.status == NotificationCampaignStatus.DONE:
            return {"status": "already_done"}

        target_ids, count = await self._resolve_audience(campaign.audience)
        campaign.target_count = count
        campaign.status = NotificationCampaignStatus.SENDING
        campaign.started_at = datetime.now(UTC)

        delivered = 0
        for i in range(0, len(target_ids), CAMPAIGN_BATCH_SIZE):
            batch = target_ids[i : i + CAMPAIGN_BATCH_SIZE]
            self.session.add_all(
                [
                    Notification(
                        user_id=uid,
                        type=NotificationType.SYSTEM.value,
                        title=campaign.title,
                        body=campaign.message,
                        data={"campaign_id": str(campaign.id), "channel": campaign.channel.value},
                    )
                    for uid in batch
                ]
            )
            await self.session.flush()
            delivered += len(batch)
            campaign.delivered_count = delivered
            await self.session.commit()

        campaign.status = NotificationCampaignStatus.DONE
        campaign.completed_at = datetime.now(UTC)
        await self.session.commit()
        return {"status": "done", "delivered": delivered}


def defer_seconds_for(schedule_at: datetime | None) -> int:
    """Seconds until the schedule time (never negative)."""
    if schedule_at is None:
        return 0
    delta = schedule_at.astimezone(UTC) - datetime.now(UTC)
    return max(int(delta.total_seconds()), 0)
