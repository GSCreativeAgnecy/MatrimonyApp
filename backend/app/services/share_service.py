from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ConflictError, NotFoundError
from app.db.models import ProfileShare, User
from app.repositories.base import BaseRepository
from app.services.audit_service import AuditService


class ShareRepository(BaseRepository[ProfileShare]):
    model = ProfileShare

    async def get_pair(self, owner: UUID, shared_with: UUID) -> ProfileShare | None:
        return await self.session.scalar(
            select(ProfileShare).where(
                ProfileShare.owner_user_id == owner,
                ProfileShare.shared_with_user_id == shared_with,
                ProfileShare.revoked_at.is_(None),
            )
        )

    async def list_for_owner(self, owner: UUID) -> list[ProfileShare]:
        stmt = (
            select(ProfileShare)
            .where(ProfileShare.owner_user_id == owner, ProfileShare.revoked_at.is_(None))
            .order_by(ProfileShare.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())


class ShareService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ShareRepository(session)
        self.audit = AuditService(session)

    async def create(
        self,
        owner: User,
        shared_with_user_id: UUID,
        *,
        permission: str = "VIEW",
        expires_in_days: int | None = None,
    ) -> ProfileShare:
        if owner.id == shared_with_user_id:
            raise ConflictError("Cannot share with yourself", code="SELF_SHARE")
        if await self.repo.get_pair(owner.id, shared_with_user_id):
            raise ConflictError("Already shared with this user", code="ALREADY_SHARED")
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
        share = await self.repo.create(
            owner_user_id=owner.id,
            shared_with_user_id=shared_with_user_id,
            permission=permission,
            expires_at=expires_at,
        )
        await self.audit.record(
            action="share.create", actor_user_id=owner.id, entity_type="share", entity_id=str(share.id)
        )
        return share

    async def revoke(self, owner: User, share_id: UUID) -> None:
        share = await self.session.get(ProfileShare, share_id)
        if share is None or share.owner_user_id != owner.id:
            raise NotFoundError("Share not found", code="SHARE_NOT_FOUND")
        share.revoked_at = datetime.now(UTC)
        await self.audit.record(
            action="share.revoke", actor_user_id=owner.id, entity_type="share", entity_id=str(share.id)
        )

    async def list_for_owner(self, owner: User) -> list[ProfileShare]:
        return await self.repo.list_for_owner(owner.id)

    async def has_active_share(self, owner_id: UUID, requester_id: UUID) -> bool:
        share = await self.repo.get_pair(owner_id, requester_id)
        if not share:
            return False
        return not (share.expires_at and share.expires_at < datetime.now(UTC))
