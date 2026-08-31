from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select

from app.db.enums import AccountStatus
from app.db.models import Photo, Profile, User
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    model = Profile

    async def get_by_user(self, user_id: UUID) -> Profile | None:
        return await self.session.scalar(select(Profile).where(Profile.user_id == user_id))

    def discovery_base_query(
        self, viewer_id: UUID, *, blocked_ids: list[UUID] | None = None, swiped_ids: list[UUID] | None = None
    ) -> Select:
        """Base query for discovery: active users with profiles, excluding self/blocked/already-swiped."""
        stmt = (
            select(Profile)
            .join(User, User.id == Profile.user_id)
            .where(
                Profile.user_id != viewer_id,
                User.account_status == AccountStatus.ACTIVE,
                User.is_banned.is_(False),
                User.deleted_at.is_(None),
            )
        )
        if blocked_ids:
            stmt = stmt.where(~Profile.user_id.in_(blocked_ids))
        if swiped_ids:
            stmt = stmt.where(~Profile.user_id.in_(swiped_ids))
        return stmt

    def age_at(self, dob: date | None) -> int | None:
        if not dob:
            return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def with_age(self, stmt: Select) -> Select:
        today = date.today()
        return stmt.add_columns(
            Profile,
            (func.extract("year", func.age(today, Profile.date_of_birth))).label("age"),
        )

    async def get_profile_photo_url(self, user_id: UUID) -> str | None:
        photo = await self.session.scalar(
            select(Photo)
            .where(Photo.user_id == user_id, Photo.is_profile_photo.is_(True), Photo.deleted_at.is_(None))
            .order_by(Photo.updated_at.desc())
            .limit(1)
        )
        return photo.url if photo else None

    async def get_primary_photos(self, user_ids: list[UUID]) -> dict[UUID, str]:
        if not user_ids:
            return {}
        stmt = (
            select(Photo.user_id, Photo.url)
            .where(Photo.user_id.in_(user_ids), Photo.is_profile_photo.is_(True), Photo.deleted_at.is_(None))
            .order_by(Photo.updated_at.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return {uid: url for uid, url in rows}
