from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ConflictError, ForbiddenError, NotFoundError
from app.db.models import Block, User
from app.repositories.match_repo import MatchRepository
from app.repositories.moderation_repo import BlockRepository
from app.repositories.user_repo import UserRepository
from app.services.audit_service import AuditService
from app.services.match_service import MatchService


class BlockService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.blocks = BlockRepository(session)
        self.users = UserRepository(session)
        self.matches = MatchRepository(session)
        self.audit = AuditService(session)

    async def block(self, blocker: User, blocked_user_id: UUID) -> Block:
        if blocker.id == blocked_user_id:
            raise ForbiddenError("You cannot block yourself", code="SELF_BLOCK")
        target = await self.users.get(blocked_user_id)
        if not target:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        existing = await self.blocks.get_pair(blocker.id, blocked_user_id)
        if existing:
            raise ConflictError("User already blocked", code="ALREADY_BLOCKED")
        block = await self.blocks.create(blocker_id=blocker.id, blocked_id=blocked_user_id)

        # A block must also end any active match with that user.
        match_service = MatchService(self.session)
        await match_service.block_and_unmatch(blocker, target)

        await self.audit.record(
            action="block.create", actor_user_id=blocker.id, entity_type="user", entity_id=str(blocked_user_id)
        )
        return block

    async def unblock(self, blocker: User, blocked_user_id: UUID) -> None:
        block = await self.blocks.get_pair(blocker.id, blocked_user_id)
        if block is None:
            raise NotFoundError("Block not found", code="BLOCK_NOT_FOUND")
        await self.blocks.delete(block)
        await self.audit.record(
            action="block.delete", actor_user_id=blocker.id, entity_type="user", entity_id=str(blocked_user_id)
        )

    async def blocked_users(self, user: User) -> list[Block]:
        from sqlalchemy import select

        stmt = select(Block).where(Block.blocker_id == user.id).order_by(Block.created_at.desc())
        return list((await self.session.execute(stmt)).scalars().all())
