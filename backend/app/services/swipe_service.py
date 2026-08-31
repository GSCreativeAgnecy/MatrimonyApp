from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ConflictError, ForbiddenError, NotFoundError
from app.db.enums import AccountStatus
from app.db.models import User
from app.repositories.match_repo import MatchRepository
from app.repositories.moderation_repo import BlockRepository
from app.repositories.swipe_repo import SwipeRepository
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService


class SwipeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.swipes = SwipeRepository(session)
        self.users = UserRepository(session)
        self.blocks = BlockRepository(session)
        self.matches = MatchRepository(session)
        self.audit = AuditService(session)
        self.notifications = NotificationService(session)

    async def _assert_can_interact(self, from_user: User, target_user: User) -> None:
        if from_user.id == target_user.id:
            raise ForbiddenError("You cannot swipe on yourself", code="SELF_SWIPE")
        if target_user.deleted_at is not None or target_user.account_status == AccountStatus.DELETED:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        if target_user.is_banned or target_user.account_status == AccountStatus.BANNED:
            raise ForbiddenError("This account is no longer available", code="USER_BANNED")
        if target_user.account_status != AccountStatus.ACTIVE:
            raise ForbiddenError("This account is not available", code="USER_UNAVAILABLE")

        blocked = await self.blocks.get_pair(from_user.id, target_user.id)
        if blocked:
            raise ForbiddenError("You cannot interact with this user", code="BLOCKED")
        # Also respect the reverse direction (they blocked you).
        if await self.blocks.get_pair(target_user.id, from_user.id):
            raise ForbiddenError("You cannot interact with this user", code="BLOCKED")

    async def swipe(self, from_user: User, target_user_id: UUID, action: str) -> dict:
        target = await self.users.get(target_user_id)
        if not target:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        await self._assert_can_interact(from_user, target)

        # Duplicate protection for LIKE/SUPER_LIKE (PASS is allowed to repeat).
        if action in {"LIKE", "SUPER_LIKE"}:
            existing = await self.swipes.liked_by(from_user.id, target_user_id)
            if existing:
                raise ConflictError("You already liked this user", code="DUPLICATE_SWIPE")

        swipe = await self.swipes.create(from_user_id=from_user.id, to_user_id=target_user_id, action=action)

        result: dict = {
            "id": str(swipe.id),
            "from_user_id": str(from_user.id),
            "to_user_id": str(target_user_id),
            "action": action,
            "created_at": swipe.created_at,
            "match_created": False,
        }

        if action in {"LIKE", "SUPER_LIKE"}:
            mutual = await self.swipes.mutual_like_exists(target_user_id, from_user.id)
            if mutual:
                existing_match = await self.matches.get_active_between(from_user.id, target_user_id)
                if existing_match:
                    raise ConflictError("You are already matched", code="ALREADY_MATCHED")
                match = await self.matches.create_between(from_user.id, target_user_id)
                result["match_created"] = True
                result["match_id"] = str(match.id)
                await self.notifications.create(
                    target_user_id, type="NEW_MATCH", title="New match", body="You have a new match!"
                )
                await self.notifications.create(
                    from_user.id, type="NEW_MATCH", title="New match", body="You have a new match!"
                )
            else:
                await self.notifications.create(
                    target_user_id, type="NEW_LIKE", title="New like", body="Someone liked your profile"
                )
        return result
