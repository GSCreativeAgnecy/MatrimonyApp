from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ForbiddenError, NotFoundError, ValidationAppError
from app.db.enums import AccountStatus, SubscriptionStatus, UserRole
from app.db.models import (
    AstrologyProfile,
    AuditLog,
    Conversation,
    ConversationParticipant,
    Family,
    JobVerification,
    Match,
    Message,
    Payment,
    Photo,
    Profile,
    Report,
    Subscription,
    User,
)
from app.repositories.user_repo import RefreshTokenRepository, UserRepository
from app.services.audit_service import AuditService
from app.services.totp_service import TotpService


def _profile_dict(p: Profile | None) -> dict | None:
    if p is None:
        return None
    return {
        "id": str(p.id),
        "first_name": p.first_name,
        "last_name": p.last_name,
        "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
        "gender": p.gender.value if p.gender else None,
        "bio": p.bio,
        "intent": p.intent.value if p.intent else None,
        "marital_status": p.marital_status.value if p.marital_status else None,
        "height_cm": p.height_cm,
        "body_type": p.body_type.value if p.body_type else None,
        "diet": p.diet.value if p.diet else None,
        "drinking": p.drinking.value if p.drinking else None,
        "smoking": p.smoking.value if p.smoking else None,
        "religion": p.religion,
        "caste": p.caste,
        "sub_caste": p.sub_caste,
        "education": p.education,
        "college": p.college,
        "field_of_study": p.field_of_study,
        "graduation_year": p.graduation_year,
        "occupation": p.occupation,
        "job_title": p.job_title,
        "workplace": p.workplace,
        "industry": p.industry,
        "annual_income": float(p.annual_income) if p.annual_income is not None else None,
        "income_currency": p.income_currency,
        "country": p.country,
        "state": p.state,
        "city": p.city,
        "hometown": p.hometown,
        "location_lat": p.location_lat,
        "location_lng": p.location_lng,
        "mother_tongue": p.mother_tongue,
        "review_status": p.review_status.value if p.review_status else None,
        "review_reason": p.review_reason,
        "reviewed_at": p.reviewed_at,
        "created_at": p.created_at,
    }


class AdminUserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)
        self.audit = AuditService(session)

    async def get_user(self, user_id: UUID) -> User:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found", code="USER_NOT_FOUND")
        return user

    # ---------- detail / sub-resources ----------

    async def detail(self, user_id: UUID) -> dict:
        user = await self.get_user(user_id)
        profile = await self.session.scalar(select(Profile).where(Profile.user_id == user.id))
        premium = await self.session.scalar(
            select(Subscription).where(
                Subscription.user_id == user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at > datetime.now(UTC),
            )
        )
        return {
            "id": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
            "account_status": user.account_status.value,
            "role": user.role.value,
            "is_banned": user.is_banned,
            "banned_at": user.banned_at,
            "suspended_at": user.suspended_at,
            "suspended_until": user.suspended_until,
            "suspended_reason": user.suspended_reason,
            "email_verified": user.email_verified_at is not None,
            "phone_verified": user.phone_verified_at is not None,
            "last_login_at": user.last_login_at,
            "last_active_at": user.last_active_at,
            "created_at": user.created_at,
            "profile": _profile_dict(profile),
            "is_premium": premium is not None,
            "subscription": {
                "id": str(premium.id),
                "status": premium.status.value,
                "starts_at": premium.starts_at,
                "expires_at": premium.expires_at,
            }
            if premium
            else None,
        }

    async def profile(self, user_id: UUID) -> dict:
        user = await self.get_user(user_id)
        profile = await self.session.scalar(select(Profile).where(Profile.user_id == user.id))
        photos = (
            (await self.session.execute(select(Photo).where(Photo.user_id == user.id, Photo.deleted_at.is_(None))))
            .scalars()
            .all()
        )
        family = await self.session.scalar(select(Family).where(Family.user_id == user.id))
        astrology = await self.session.scalar(select(AstrologyProfile).where(AstrologyProfile.user_id == user.id))
        return {
            "user_id": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
            "account_status": user.account_status.value,
            "role": user.role.value,
            "profile": _profile_dict(profile),
            "photos": [
                {
                    "id": str(ph.id),
                    "url": ph.url,
                    "thumbnail_url": ph.thumbnail_url,
                    "position": ph.position,
                    "is_profile_photo": ph.is_profile_photo,
                    "verification_status": ph.verification_status.value,
                    "uploaded_at": ph.uploaded_at,
                }
                for ph in photos
            ],
            "family": {
                "family_type": family.family_type.value if family and family.family_type else None,
                "family_values": family.family_values.value if family and family.family_values else None,
                "about_family": family.about_family if family else None,
                "family_location": family.family_location if family else None,
            }
            if family
            else None,
            "astrology": {
                "rashi": astrology.rashi.value if astrology and astrology.rashi else None,
                "nakshatra": astrology.nakshatra.value if astrology and astrology.nakshatra else None,
                "gothram": astrology.gothram if astrology else None,
                "dosham": astrology.dosham.value if astrology and astrology.dosham else None,
                "time_of_birth": astrology.time_of_birth if astrology else None,
                "place_of_birth": astrology.place_of_birth if astrology else None,
                "horoscope_verified": bool(astrology and astrology.horoscope_verified),
            }
            if astrology
            else None,
        }

    async def photos(self, user_id: UUID) -> list[dict]:
        user = await self.get_user(user_id)
        photos = (
            (await self.session.execute(select(Photo).where(Photo.user_id == user.id, Photo.deleted_at.is_(None))))
            .scalars()
            .all()
        )
        return [
            {
                "id": str(ph.id),
                "url": ph.url,
                "thumbnail_url": ph.thumbnail_url,
                "position": ph.position,
                "is_profile_photo": ph.is_profile_photo,
                "verification_status": ph.verification_status.value,
                "mime_type": ph.mime_type,
                "uploaded_at": ph.uploaded_at,
            }
            for ph in photos
        ]

    async def verifications(self, user_id: UUID) -> list[dict]:
        user = await self.get_user(user_id)
        rows = (
            (await self.session.execute(select(JobVerification).where(JobVerification.user_id == user.id)))
            .scalars()
            .all()
        )
        return [
            {
                "id": str(v.id),
                "employment_type": v.employment_type.value,
                "employer_name": v.employer_name,
                "job_title": v.job_title,
                "country": v.country,
                "verification_status": v.verification_status.value,
                "amount_paid": float(v.amount_paid) if v.amount_paid is not None else None,
                "submitted_at": v.submitted_at,
                "verified_at": v.verified_at,
                "expires_at": v.expires_at,
                "reviewer_notes": v.reviewer_notes,
                "rejection_reason": v.rejection_reason,
            }
            for v in rows
        ]

    async def matches(self, user_id: UUID) -> list[dict]:
        user = await self.get_user(user_id)
        rows = (
            (
                await self.session.execute(
                    select(Match)
                    .where(or_(Match.user1_id == user.id, Match.user2_id == user.id))
                    .order_by(Match.matched_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": str(m.id),
                "user1_id": str(m.user1_id),
                "user2_id": str(m.user2_id),
                "status": m.status.value,
                "matched_at": m.matched_at,
                "unmatched_at": m.unmatched_at,
            }
            for m in rows
        ]

    async def conversations(self, user_id: UUID) -> list[dict]:
        user = await self.get_user(user_id)
        conv_ids = (
            (
                await self.session.execute(
                    select(ConversationParticipant.conversation_id).where(ConversationParticipant.user_id == user.id)
                )
            )
            .scalars()
            .all()
        )
        if not conv_ids:
            return []
        convs = (
            (
                await self.session.execute(
                    select(Conversation)
                    .where(Conversation.id.in_(conv_ids))
                    .order_by(Conversation.last_message_at.desc().nullslast())
                )
            )
            .scalars()
            .all()
        )
        result = []
        for conv in convs:
            participants = (
                (
                    await self.session.execute(
                        select(ConversationParticipant).where(ConversationParticipant.conversation_id == conv.id)
                    )
                )
                .scalars()
                .all()
            )
            count = await self.session.scalar(
                select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
            )
            result.append(
                {
                    "id": str(conv.id),
                    "participant_ids": [str(p.user_id) for p in participants],
                    "last_message_at": conv.last_message_at,
                    "message_count": int(count or 0),
                    "created_at": conv.created_at,
                }
            )
        return result

    async def payments(self, user_id: UUID) -> list[dict]:
        user = await self.get_user(user_id)
        rows = (
            (
                await self.session.execute(
                    select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": str(p.id),
                "amount": float(p.amount),
                "currency": p.currency,
                "payment_type": p.payment_type,
                "status": p.status.value,
                "provider": p.provider,
                "provider_payment_id": p.provider_payment_id,
                "created_at": p.created_at,
                "paid_at": p.paid_at,
            }
            for p in rows
        ]

    async def reports(self, user_id: UUID) -> list[dict]:
        user = await self.get_user(user_id)
        rows = (
            (
                await self.session.execute(
                    select(Report)
                    .where(or_(Report.reporter_id == user.id, Report.reported_user_id == user.id))
                    .order_by(Report.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": str(r.id),
                "reporter_id": str(r.reporter_id),
                "reported_user_id": str(r.reported_user_id),
                "reason": r.reason,
                "description": r.description,
                "status": r.status,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    async def audit_trail(self, user_id: UUID, *, limit: int = 50) -> list[dict]:
        user = await self.get_user(user_id)
        rows = (
            (
                await self.session.execute(
                    select(AuditLog)
                    .where(
                        or_(
                            AuditLog.actor_user_id == user.id,
                            AuditLog.entity_type == "user",
                            AuditLog.entity_id == str(user.id),
                        )
                    )
                    .order_by(AuditLog.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "id": str(a.id),
                "action": a.action,
                "actor_user_id": str(a.actor_user_id) if a.actor_user_id else None,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "details": a.meta,
                "ip_address": a.ip_address,
                "user_agent": a.user_agent,
                "created_at": a.created_at,
            }
            for a in rows
        ]

    # ---------- actions ----------

    async def suspend(
        self,
        admin: User,
        user_id: UUID,
        *,
        reason: str,
        duration_minutes: int | None,
        notes: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN} and admin.id != user.id:
            raise ForbiddenError("Admins cannot be suspended by another admin", code="FORBIDDEN")
        if user.account_status == AccountStatus.DELETED:
            raise ValidationAppError("Cannot suspend a deleted account", code="ACCOUNT_DELETED")
        user.account_status = AccountStatus.SUSPENDED
        user.suspended_at = datetime.now(UTC)
        user.suspended_until = datetime.now(UTC) + timedelta(minutes=duration_minutes) if duration_minutes else None
        user.suspended_reason = reason
        user.suspended_by = admin.id
        await self.refresh_repo.revoke_all_for_user(user.id)
        await self.audit.record(
            action="admin.suspend",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            metadata={"reason": reason, "duration_minutes": duration_minutes, "notes": notes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def ban(
        self,
        admin: User,
        user_id: UUID,
        *,
        reason: str,
        notes: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN} and admin.id != user.id:
            raise ForbiddenError("Admins cannot be banned by another admin", code="FORBIDDEN")
        user.is_banned = True
        user.banned_at = datetime.now(UTC)
        user.account_status = AccountStatus.BANNED
        await self.refresh_repo.revoke_all_for_user(user.id)
        await self.audit.record(
            action="admin.ban",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            metadata={"reason": reason, "notes": notes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def unban(
        self, admin: User, user_id: UUID, *, ip_address: str | None = None, user_agent: str | None = None
    ) -> User:
        user = await self.get_user(user_id)
        user.is_banned = False
        user.banned_at = None
        user.account_status = AccountStatus.ACTIVE
        await self.audit.record(
            action="admin.unban",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def delete_user(
        self,
        admin: User,
        user_id: UUID,
        *,
        reason: str,
        notes: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
            raise ForbiddenError("Admins cannot be deleted", code="FORBIDDEN")
        user.deleted_at = datetime.now(UTC)
        user.account_status = AccountStatus.DELETED
        await self.refresh_repo.revoke_all_for_user(user.id)
        await self.audit.record(
            action="admin.delete_user",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            metadata={"reason": reason, "notes": notes},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def restore(
        self, admin: User, user_id: UUID, *, ip_address: str | None = None, user_agent: str | None = None
    ) -> User:
        user = await self.get_user(user_id)
        user.deleted_at = None
        user.account_status = AccountStatus.ACTIVE
        await self.audit.record(
            action="admin.restore_user",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def verify(
        self,
        admin: User,
        user_id: UUID,
        *,
        kind: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if kind == "email":
            user.email_verified_at = datetime.now(UTC)
        elif kind == "phone":
            user.phone_verified_at = datetime.now(UTC)
        else:
            raise ValidationAppError("kind must be 'email' or 'phone'", code="INVALID_VERIFY_KIND")
        await self.audit.record(
            action="admin.verify",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            metadata={"kind": kind},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def change_role(
        self,
        admin: User,
        user_id: UUID,
        new_role: UserRole,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = await self.get_user(user_id)
        if user.id == admin.id and user.role == UserRole.SUPER_ADMIN and new_role != UserRole.SUPER_ADMIN:
            raise ForbiddenError("A SUPER_ADMIN cannot demote themselves", code="FORBIDDEN")
        if user.role == UserRole.SUPER_ADMIN and admin.role != UserRole.SUPER_ADMIN:
            raise ForbiddenError("Only a SUPER_ADMIN can change a SUPER_ADMIN", code="FORBIDDEN")
        if new_role == UserRole.SUPER_ADMIN and admin.role != UserRole.SUPER_ADMIN:
            raise ForbiddenError("Only a SUPER_ADMIN can grant SUPER_ADMIN", code="FORBIDDEN")
        old_role = user.role.value
        user.role = new_role
        await self.audit.record(
            action="admin.role_change",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
            metadata={"old_role": old_role, "new_role": new_role.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def revoke_sessions(self, admin: User, user_id: UUID) -> None:
        user = await self.get_user(user_id)
        await self.refresh_repo.revoke_all_for_user(user.id)
        await self.audit.record(
            action="admin.revoke_sessions",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user.id),
        )

    async def reset_2fa(self, admin: User, user_id: UUID) -> None:
        user = await self.get_user(user_id)
        await TotpService(self.session).admin_reset(admin, user.id)
