from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import NotFoundError
from app.db.models import Family, FamilyMember
from app.repositories.base import BaseRepository


class FamilyRepository(BaseRepository[Family]):
    model = Family

    async def get_for_user(self, user_id: UUID) -> Family | None:
        return await self.session.scalar(select(Family).where(Family.user_id == user_id))


class FamilyMemberRepository(BaseRepository[FamilyMember]):
    model = FamilyMember

    async def list_for_user(self, user_id: UUID) -> list[FamilyMember]:
        stmt = select(FamilyMember).where(FamilyMember.user_id == user_id).order_by(FamilyMember.created_at)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_for_user(self, member_id: UUID, user_id: UUID) -> FamilyMember | None:
        return await self.session.scalar(
            select(FamilyMember).where(FamilyMember.id == member_id, FamilyMember.user_id == user_id)
        )


class FamilyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.families = FamilyRepository(session)
        self.members = FamilyMemberRepository(session)

    async def get_family(self, user_id: UUID) -> Family:
        family = await self.families.get_for_user(user_id)
        if family is None:
            family = Family(user_id=user_id)
            self.session.add(family)
            await self.session.flush()
        return family

    async def update_family(self, user_id: UUID, data: dict) -> Family:
        family = await self.get_family(user_id)
        for field, value in data.items():
            if value is not None:
                setattr(family, field, value)
        return family

    async def list_members(self, user_id: UUID) -> list[FamilyMember]:
        return await self.members.list_for_user(user_id)

    async def add_member(self, user_id: UUID, data: dict) -> FamilyMember:
        return await self.members.create(user_id=user_id, **data)

    async def update_member(self, user_id: UUID, member_id: UUID, data: dict) -> FamilyMember:
        member = await self.members.get_for_user(member_id, user_id)
        if member is None:
            raise NotFoundError("Family member not found", code="FAMILY_MEMBER_NOT_FOUND")
        for field, value in data.items():
            if value is not None:
                setattr(member, field, value)
        return member

    async def delete_member(self, user_id: UUID, member_id: UUID) -> None:
        member = await self.members.get_for_user(member_id, user_id)
        if member is None:
            raise NotFoundError("Family member not found", code="FAMILY_MEMBER_NOT_FOUND")
        await self.members.delete(member)
