from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, asc, desc, exists, func, or_, select

from app.db.enums import SubscriptionStatus
from app.db.models import Photo, Profile, RefreshTokenRecord, Subscription, User, UserPrivacySettings
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone_number == phone, User.deleted_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_email_or_phone(self, email: str | None, phone: str | None) -> User | None:
        if email and phone:
            stmt = select(User).where(or_(User.email == email, User.phone_number == phone), User.deleted_at.is_(None))
        elif email:
            return await self.get_by_email(email)
        else:
            return await self.get_by_phone(phone) if phone else None
        return (await self.session.execute(stmt)).scalars().first()

    async def ensure_profile(self, user_id: UUID) -> Profile:
        profile = await self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            profile = Profile(user_id=user_id)
            self.session.add(profile)
            await self.session.flush()
        return profile

    async def get_privacy(self, user_id: UUID) -> UserPrivacySettings:
        settings = await self.session.scalar(select(UserPrivacySettings).where(UserPrivacySettings.user_id == user_id))
        if settings is None:
            settings = UserPrivacySettings(user_id=user_id)
            self.session.add(settings)
            await self.session.flush()
        return settings

    # ---------- admin ----------

    async def admin_search(
        self,
        *,
        search: str | None = None,
        gender: str | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        religion: str | None = None,
        caste: str | None = None,
        education: str | None = None,
        occupation: str | None = None,
        premium: bool | None = None,
        verified: bool | None = None,
        account_status: list[str] | None = None,
        registered_from: datetime | None = None,
        registered_to: datetime | None = None,
        active_from: datetime | None = None,
        active_to: datetime | None = None,
        sort: str = "created_at",
        order: str = "desc",
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        profile = Profile
        premium_exists = exists().where(
            Subscription.user_id == User.id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > datetime.now(UTC),
        )
        stmt = select(User, profile).outerjoin(profile, profile.user_id == User.id)
        count_stmt = select(func.count()).select_from(User).outerjoin(profile, profile.user_id == User.id)

        conds = []
        if search:
            like = f"%{search}%"
            conds.append(
                or_(
                    User.email.ilike(like),
                    User.phone_number.ilike(like),
                    profile.first_name.ilike(like),
                    profile.last_name.ilike(like),
                )
            )
        if gender:
            conds.append(profile.gender == gender)
        if age_min is not None:
            conds.append(profile.date_of_birth <= date.today() - timedelta(days=365 * age_min))
        if age_max is not None:
            conds.append(profile.date_of_birth >= date.today() - timedelta(days=365 * (age_max + 1)))
        if city:
            conds.append(profile.city.ilike(f"%{city}%"))
        if state:
            conds.append(profile.state.ilike(f"%{state}%"))
        if country:
            conds.append(profile.country.ilike(f"%{country}%"))
        if religion:
            conds.append(profile.religion.ilike(f"%{religion}%"))
        if caste:
            conds.append(profile.caste.ilike(f"%{caste}%"))
        if education:
            conds.append(profile.education.ilike(f"%{education}%"))
        if occupation:
            conds.append(profile.occupation.ilike(f"%{occupation}%"))
        if premium is not None:
            conds.append(premium_exists if premium else ~premium_exists)
        if verified is not None:
            if verified:
                conds.append(or_(User.email_verified_at.is_not(None), User.phone_verified_at.is_not(None)))
            else:
                conds.append(and_(User.email_verified_at.is_(None), User.phone_verified_at.is_(None)))
        if account_status:
            conds.append(User.account_status.in_(account_status))
        if registered_from is not None:
            conds.append(User.created_at >= registered_from)
        if registered_to is not None:
            conds.append(User.created_at < registered_to + timedelta(days=1))
        if active_from is not None:
            conds.append(User.last_active_at >= active_from)
        if active_to is not None:
            conds.append(User.last_active_at < active_to + timedelta(days=1))

        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)

        total = int((await self.session.execute(count_stmt)).scalar_one())

        sort_columns = {
            "created_at": User.created_at,
            "last_active_at": User.last_active_at,
            "email": User.email,
            "account_status": User.account_status,
        }
        sort_col = sort_columns.get(sort, User.created_at)
        stmt = stmt.order_by(desc(sort_col) if order == "desc" else asc(sort_col))
        stmt = stmt.limit(limit).offset(offset)
        rows = (await self.session.execute(stmt)).all()

        user_ids = [u.id for u, _ in rows]
        photos = await self._primary_photo_map(user_ids)
        premium_ids = await self._premium_user_ids(user_ids)
        return [self._serialize_row(u, p, photos.get(u.id), u.id in premium_ids) for u, p in rows], total

    async def _primary_photo_map(self, user_ids: list[UUID]) -> dict[UUID, str | None]:
        if not user_ids:
            return {}
        rows = (
            await self.session.execute(
                select(Photo.user_id, Photo.url).where(
                    Photo.user_id.in_(user_ids),
                    Photo.deleted_at.is_(None),
                    Photo.verification_status != "REJECTED",
                )
            )
        ).all()
        return {uid: url for uid, url in rows}

    async def _premium_user_ids(self, user_ids: list[UUID]) -> set[UUID]:
        if not user_ids:
            return set()
        rows = (
            (
                await self.session.execute(
                    select(Subscription.user_id).where(
                        Subscription.user_id.in_(user_ids),
                        Subscription.status == SubscriptionStatus.ACTIVE,
                        Subscription.expires_at > datetime.now(UTC),
                    )
                )
            )
            .scalars()
            .all()
        )
        return set(rows)

    @staticmethod
    def _serialize_row(user: User, profile: Profile | None, photo_url: str | None, is_premium: bool) -> dict:
        age = None
        if profile and profile.date_of_birth:
            age = (date.today() - profile.date_of_birth).days // 365
        return {
            "id": str(user.id),
            "name": " ".join(
                n for n in ((profile.first_name if profile else None), (profile.last_name if profile else None)) if n
            )
            or None,
            "email": user.email,
            "phone_number": user.phone_number,
            "gender": profile.gender.value if profile and profile.gender else None,
            "age": age,
            "city": profile.city if profile else None,
            "state": profile.state if profile else None,
            "country": profile.country if profile else None,
            "religion": profile.religion if profile else None,
            "caste": profile.caste if profile else None,
            "education": profile.education if profile else None,
            "occupation": profile.occupation if profile else None,
            "role": user.role.value,
            "account_status": user.account_status.value,
            "is_banned": user.is_banned,
            "is_premium": is_premium,
            "verified": bool(user.email_verified_at or user.phone_verified_at),
            "profile_photo": photo_url,
            "last_active_at": user.last_active_at,
            "created_at": user.created_at,
        }


class RefreshTokenRepository(BaseRepository[RefreshTokenRecord]):
    model = RefreshTokenRecord

    async def get_active(self, jti: str) -> RefreshTokenRecord | None:
        stmt = select(RefreshTokenRecord).where(RefreshTokenRecord.jti == jti, RefreshTokenRecord.revoked_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def revoke(self, record: RefreshTokenRecord, *, replaced_by: str | None = None) -> None:
        from datetime import datetime

        record.revoked_at = datetime.now(UTC)
        if replaced_by:
            record.replaced_by_jti = replaced_by

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        from datetime import datetime

        stmt = select(RefreshTokenRecord).where(
            RefreshTokenRecord.user_id == user_id, RefreshTokenRecord.revoked_at.is_(None)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        now = datetime.now(UTC)
        for row in rows:
            row.revoked_at = now
