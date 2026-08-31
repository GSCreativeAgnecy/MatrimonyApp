from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ForbiddenError, NotFoundError
from app.db.enums import MatchStatus
from app.db.models import Match, User
from app.repositories.match_repo import MatchRepository
from app.repositories.moderation_repo import BlockRepository
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService


class MatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.matches = MatchRepository(session)
        self.users = UserRepository(session)
        self.blocks = BlockRepository(session)
        self.audit = AuditService(session)

    async def list_for(self, user: User) -> list[Match]:
        return await self.matches.matches_for(user.id)

    async def get_active_between(self, a: UUID, b: UUID) -> Match | None:
        return await self.matches.get_active_between(a, b)

    async def get_for_user(self, user: User, match_id: UUID) -> Match:
        match = await self.session.get(Match, match_id)
        if match is None:
            raise NotFoundError("Match not found", code="MATCH_NOT_FOUND")
        if match.user1_id != user.id and match.user2_id != user.id:
            raise ForbiddenError("Not your match", code="FORBIDDEN")
        return match

    async def other_user(self, match: Match, me: UUID) -> User:
        other_id = self.matches.other_user_id(match, me)
        other = await self.users.get(other_id)
        if other is None:
            raise NotFoundError("Matched user not found", code="USER_NOT_FOUND")
        return other

    async def unmatch(self, user: User, match_id: UUID) -> None:
        match = await self.get_for_user(user, match_id)
        match.status = MatchStatus.UNMATCHED
        match.unmatched_at = datetime.now(UTC)
        await self.audit.record(
            action="match.unmatch", actor_user_id=user.id, entity_type="match", entity_id=str(match.id)
        )

    async def block_and_unmatch(self, blocker: User, blocked: User) -> None:
        match = await self.matches.get_active_between(blocker.id, blocked.id)
        if match:
            match.status = MatchStatus.BLOCKED
            match.unmatched_at = datetime.now(UTC)
