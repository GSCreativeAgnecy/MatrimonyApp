import math
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import NotFoundError
from app.db.enums import AccountStatus
from app.db.models import Profile, User
from app.repositories.match_repo import MatchRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.user_repo import UserRepository
from app.schemas.profile import PublicProfileResponse
from app.services.audit_service import AuditService


def _age(dob: date | None) -> int | None:
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def distance_km(lat1: float | None, lng1: float | None, lat2: float | None, lng2: float | None) -> float | None:
    """Haversine approximate distance in km. None if coordinates missing."""
    if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProfileRepository(session)
        self.users = UserRepository(session)
        self.matches = MatchRepository(session)
        self.audit = AuditService(session)

    # ---------- own profile ----------

    async def ensure_profile(self, user: User) -> Profile:
        return await self.users.ensure_profile(user.id)

    async def get_own(self, user: User) -> Profile:
        return await self.ensure_profile(user)

    async def create(self, user: User, data: dict[str, Any]) -> Profile:
        if user.account_status == AccountStatus.PENDING:
            user.account_status = AccountStatus.ACTIVE
        profile = await self.users.ensure_profile(user.id)
        for field, value in data.items():
            if value is not None:
                setattr(profile, field, value)
        await self.audit.record(
            action="profile.update", actor_user_id=user.id, entity_type="profile", entity_id=profile.id
        )
        return profile

    async def update(self, user: User, data: dict[str, Any]) -> Profile:
        profile = await self.ensure_profile(user)
        for field, value in data.items():
            setattr(profile, field, value)
        await self.audit.record(
            action="profile.update", actor_user_id=user.id, entity_type="profile", entity_id=profile.id
        )
        return profile

    async def delete_account(self, user: User) -> None:

        user.deleted_at = datetime.now(UTC)
        user.account_status = AccountStatus.DELETED
        await self.audit.record(action="user.delete", actor_user_id=user.id, entity_type="user", entity_id=user.id)

    # ---------- viewing others ----------

    async def get_target_user(self, target_user_id: UUID) -> User:
        user = await self.users.get(target_user_id)
        if not user or user.deleted_at is not None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        return user

    async def matched_pair_ids(self, user_id: UUID) -> set[UUID]:
        matches = await self.matches.matches_for(user_id)
        ids = set()
        for m in matches:
            ids.add(m.user1_id)
            ids.add(m.user2_id)
        return ids - {user_id}

    async def serialize_public(
        self,
        viewer: User,
        target: User,
        profile: Profile,
        *,
        matched: bool = False,
        distance_to_viewer: float | None = None,
        photo_url: str | None = None,
    ) -> PublicProfileResponse:
        privacy = await self.users.get_privacy(target.id)
        show_distance = privacy.show_distance and distance_to_viewer is not None

        now = datetime.now(UTC)
        last_seen = None
        if privacy.show_last_seen and target.last_active_at:
            delta = (now - target.last_active_at).total_seconds()
            if delta < 3600:
                last_seen = f"{int(delta // 60)}m ago"
            elif delta < 86400:
                last_seen = f"{int(delta // 3600)}h ago"
            else:
                last_seen = f"{int(delta // 86400)}d ago"

        base: dict[str, Any] = {
            "id": str(profile.id),
            "user_id": str(target.id),
            "first_name": profile.first_name,
            "gender": profile.gender.value if profile.gender else None,
            "age": _age(profile.date_of_birth),
            "marital_status": profile.marital_status.value if profile.marital_status else None,
            "religion": profile.religion,
            "caste": profile.caste,
            "mother_tongue": profile.mother_tongue,
            "education": profile.education,
            "occupation": profile.occupation,
            "job_title": profile.job_title,
            "city": profile.city,
            "state": profile.state,
            "country": profile.country,
            "distance_km": distance_to_viewer if show_distance else None,
            "bio": profile.bio,
            "intent": profile.intent.value if profile.intent else None,
            "diet": profile.diet.value if profile.diet else None,
            "drinking": profile.drinking.value if profile.drinking else None,
            "smoking": profile.smoking.value if profile.smoking else None,
            "height_cm": profile.height_cm,
            "body_type": profile.body_type.value if profile.body_type else None,
            "profile_photo": photo_url,
            "last_seen": last_seen if privacy.show_online_status else None,
            "is_online": False,
            "is_verified_photo": False,
            "is_verified_job": False,
        }

        if matched:
            base["phone_number"] = target.phone_number
            base["email"] = target.email
            base["workplace"] = profile.workplace
            base["is_online"] = target.last_active_at and (now - target.last_active_at).total_seconds() < 120

        return PublicProfileResponse(**base)

    # ---------- admin moderation ----------

    async def admin_list(
        self,
        *,
        search: str | None = None,
        incomplete: bool | None = None,
        reported: bool | None = None,
        review_status: str | None = None,
        recently_updated: bool | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        from sqlalchemy import exists, func, or_, select

        from app.db.models import Photo, Report

        reported_exists = exists().where(Report.reported_user_id == Profile.user_id)
        stmt = select(Profile, User.email).join(User, User.id == Profile.user_id)
        count_stmt = select(func.count()).select_from(Profile).join(User, User.id == Profile.user_id)
        conds = []
        if search:
            like = f"%{search}%"
            conds.append(
                or_(
                    Profile.first_name.ilike(like),
                    Profile.last_name.ilike(like),
                    User.email.ilike(like),
                    User.phone_number.ilike(like),
                )
            )
        if incomplete:
            conds.append(Profile.first_name.is_(None))
        if reported:
            conds.append(reported_exists)
        if review_status:
            conds.append(Profile.review_status == review_status)
        if recently_updated:
            conds.append(Profile.updated_at > datetime.now(UTC) - timedelta(days=7))

        for c in conds:
            stmt = stmt.where(c)
            count_stmt = count_stmt.where(c)

        total = int((await self.session.execute(count_stmt)).scalar_one())
        rows = (await self.session.execute(stmt.order_by(Profile.updated_at.desc()).limit(limit).offset(offset))).all()
        user_ids = [p.user_id for p, _ in rows]
        photo_map = {}
        if user_ids:
            photo_rows = (
                await self.session.execute(
                    select(Photo.user_id, Photo.url).where(
                        Photo.user_id.in_(user_ids),
                        Photo.deleted_at.is_(None),
                        Photo.verification_status != "REJECTED",
                    )
                )
            ).all()
            photo_map = {uid: url for uid, url in photo_rows}
        return (
            [
                {
                    "user_id": str(p.user_id),
                    "email": email,
                    "name": " ".join(n for n in (p.first_name, p.last_name) if n) or None,
                    "gender": p.gender.value if p.gender else None,
                    "age": _age(p.date_of_birth),
                    "city": p.city,
                    "country": p.country,
                    "religion": p.religion,
                    "occupation": p.occupation,
                    "review_status": p.review_status.value if p.review_status else None,
                    "completeness": round(
                        (sum(1 for f in self._required_fields() if getattr(p, f, None)) / len(self._required_fields()))
                        * 100
                    ),
                    "profile_photo": photo_map.get(p.user_id),
                    "updated_at": p.updated_at,
                }
                for p, email in rows
            ],
            total,
        )

    @staticmethod
    def _required_fields() -> list[str]:
        return [
            "first_name",
            "date_of_birth",
            "gender",
            "religion",
            "caste",
            "education",
            "occupation",
            "city",
            "country",
        ]

    async def moderate(
        self,
        admin: User,
        user_id: UUID,
        *,
        action: str,
        reason: str | None = None,
    ) -> Profile:
        from datetime import UTC

        from app.api.errors import ValidationAppError
        from app.db.enums import ProfileReviewStatus

        mapping = {
            "approve": ProfileReviewStatus.APPROVED,
            "reject": ProfileReviewStatus.REJECTED,
            "request_changes": ProfileReviewStatus.REQUEST_CHANGES,
            "suspend_profile": ProfileReviewStatus.SUSPENDED,
        }
        if action not in mapping:
            raise ValidationAppError(
                "action must be approve|reject|request_changes|suspend_profile", code="INVALID_ACTION"
            )
        profile = await self.session.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            raise NotFoundError("Profile not found", code="PROFILE_NOT_FOUND")
        profile.review_status = mapping[action]
        profile.reviewed_by = admin.id
        profile.reviewed_at = datetime.now(UTC)
        profile.review_reason = reason
        await self.audit.record(
            action="profile.moderate",
            actor_user_id=admin.id,
            entity_type="profile",
            entity_id=str(profile.id),
            metadata={"action": action, "reason": reason},
        )
        return profile
