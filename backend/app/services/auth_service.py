import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationAppError
from app.config.settings import settings
from app.db.enums import AccountStatus, UserRole
from app.db.models import User
from app.repositories.user_repo import RefreshTokenRepository, UserRepository
from app.security.jwt import TokenError, create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password, verify_password
from app.security.redis import get_redis
from app.services.audit_service import AuditService
from app.workers.enqueue import enqueue_email, enqueue_sms

OTP_TTL_SECONDS = 600
RESET_TTL_SECONDS = 1800
VERIFY_TTL_SECONDS = 3600


async def _redis_setex(key: str, seconds: int, value: str) -> None:
    """Best-effort Redis write. Never blocks critical flows if Redis is down."""
    try:
        redis = await get_redis()
        await redis.setex(key, seconds, value)
    except Exception:
        logging.getLogger("app.auth").warning("Redis unavailable for %s", key, exc_info=True)


async def _redis_get(key: str) -> str | None:
    try:
        redis = await get_redis()
        return await redis.get(key)
    except Exception:
        logging.getLogger("app.auth").warning("Redis unavailable for %s", key, exc_info=True)
        return None


async def _redis_delete(key: str) -> None:
    try:
        redis = await get_redis()
        await redis.delete(key)
    except Exception:
        logging.getLogger("app.auth").warning("Redis unavailable for %s", key, exc_info=True)


def _now() -> datetime:
    return datetime.now(UTC)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_repo = RefreshTokenRepository(session)
        self.audit = AuditService(session)

    # ---------- registration / login ----------

    async def register(self, *, email: str | None, phone_number: str | None, password: str) -> User:
        if not email and not phone_number:
            raise ValidationAppError("Provide an email or phone number")
        existing = await self.users.get_by_email_or_phone(email, phone_number)
        if existing:
            raise ConflictError("An account with this email/phone already exists", code="ACCOUNT_EXISTS")

        user = await self.users.create(
            email=email.lower() if email else None,
            phone_number=phone_number,
            password_hash=hash_password(password),
            account_status=AccountStatus.ACTIVE,
            role=UserRole.USER,
        )
        await self.audit.record(action="auth.register", actor_user_id=user.id, entity_type="user", entity_id=user.id)
        await self._send_verification(user)
        return user

    async def login(self, *, email: str | None, phone_number: str | None, password: str) -> tuple[User, bool]:
        """Validate credentials.

        Returns ``(user, mfa_required)``. When ``mfa_required`` is true the caller
        must complete two-factor authentication before any token is issued.
        """
        user = await self.users.get_by_email_or_phone(email, phone_number)
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials", code="INVALID_CREDENTIALS")
        await self._assert_login_allowed(user)

        from app.services.totp_service import TotpService

        mfa_required = await TotpService(self.session).is_enabled(user.id)
        user.last_login_at = _now()
        await self.audit.record(action="auth.login", actor_user_id=user.id, entity_type="user", entity_id=user.id)
        return user, mfa_required

    async def complete_mfa_login(self, mfa_token: str, code: str) -> dict:
        """Verify a TOTP/recovery code after a password login and issue tokens."""
        try:
            payload = decode_token(mfa_token, "mfa")
        except TokenError as exc:
            raise UnauthorizedError(str(exc), code="INVALID_MFA_TOKEN") from exc

        from app.services.totp_service import TotpService

        user = await self.users.get(UUID(payload["sub"]))
        if user is None:
            raise UnauthorizedError("Account not found", code="NOT_AUTHENTICATED")
        totp = TotpService(self.session)
        if not await totp.is_enabled(user.id):
            raise UnauthorizedError("Two-factor authentication is not enabled", code="MFA_NOT_ENABLED")
        if not await totp.verify(user, code):
            raise UnauthorizedError("Invalid verification code", code="INVALID_TOTP")
        await self.audit.record(
            action="auth.mfa_completed", actor_user_id=user.id, entity_type="user", entity_id=user.id
        )
        return await self.create_token_pair(user.id)

    async def _assert_login_allowed(self, user: User) -> None:
        if user.deleted_at is not None or user.account_status == AccountStatus.DELETED:
            raise UnauthorizedError("This account has been deleted", code="ACCOUNT_DELETED")
        if user.is_banned or user.account_status == AccountStatus.BANNED:
            raise UnauthorizedError("This account has been banned", code="ACCOUNT_BANNED")
        if user.account_status == AccountStatus.SUSPENDED:
            raise UnauthorizedError("This account is suspended", code="ACCOUNT_SUSPENDED")

    # ---------- tokens ----------

    async def create_token_pair(self, user_id: UUID) -> dict:
        access_token = create_access_token(str(user_id))
        refresh_token, jti, expires_at = create_refresh_token(str(user_id))
        await self.refresh_repo.create(user_id=user_id, jti=jti, expires_at=expires_at)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token, "refresh")
        except TokenError as exc:
            raise UnauthorizedError(str(exc), code="INVALID_REFRESH_TOKEN") from exc
        user_id = UUID(payload["sub"])
        jti = payload["jti"]

        record = await self.refresh_repo.get_active(jti)
        expires_at = record.expires_at if record else None
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if record is None or record.user_id != user_id or expires_at is None or expires_at < _now():
            raise UnauthorizedError("Refresh token has been revoked", code="TOKEN_REVOKED")

        # Rotation: revoke this token, mint a new one.
        new_pair = await self.create_token_pair(user_id)
        await self.refresh_repo.revoke(record, replaced_by=decode_token(new_pair["refresh_token"], "refresh")["jti"])
        return new_pair

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, "refresh")
        except TokenError as exc:
            raise UnauthorizedError(str(exc), code="INVALID_REFRESH_TOKEN") from exc
        record = await self.refresh_repo.get_active(payload["jti"])
        if record:
            await self.refresh_repo.revoke(record)
            await self.audit.record(
                action="auth.logout", actor_user_id=record.user_id, entity_type="user", entity_id=record.user_id
            )

    async def revoke_all(self, user_id: UUID) -> None:
        await self.refresh_repo.revoke_all_for_user(user_id)

    # ---------- password ----------

    async def forgot_password(self, *, email: str | None, phone_number: str | None) -> None:
        user = await self.users.get_by_email_or_phone(email, phone_number)
        # Always succeed (do not leak which accounts exist).
        if not user:
            return
        token = secrets.token_urlsafe(32)
        await _redis_setex(f"reset:{token}", RESET_TTL_SECONDS, str(user.id))
        if user.email:
            await enqueue_email(user.email, "Reset your password", f"Reset token: {token}")
        if user.phone_number:
            await enqueue_sms(user.phone_number, f"Your password reset code: {token}")

    async def reset_password(self, token: str, new_password: str) -> None:
        user_id_raw = await _redis_get(f"reset:{token}")
        if not user_id_raw:
            raise UnauthorizedError("Invalid or expired reset token", code="INVALID_RESET_TOKEN")
        await _redis_delete(f"reset:{token}")
        user = await self.users.get(UUID(user_id_raw))
        if not user:
            raise NotFoundError("User not found")
        user.password_hash = hash_password(new_password)
        await self.revoke_all(user.id)
        await self.audit.record(
            action="auth.password_reset", actor_user_id=user.id, entity_type="user", entity_id=user.id
        )

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        if not user.password_hash or not verify_password(old_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect", code="INVALID_PASSWORD")
        user.password_hash = hash_password(new_password)
        await self.audit.record(
            action="auth.password_change", actor_user_id=user.id, entity_type="user", entity_id=user.id
        )

    # ---------- email / phone verification ----------

    async def _send_verification(self, user: User) -> None:
        if user.email:
            token = secrets.token_urlsafe(32)
            await _redis_setex(f"email_verify:{token}", VERIFY_TTL_SECONDS, str(user.id))
            await enqueue_email(user.email, "Verify your email", f"Verify link token: {token}")

    async def verify_email(self, token: str) -> None:
        user_id_raw = await _redis_get(f"email_verify:{token}")
        if not user_id_raw:
            raise UnauthorizedError("Invalid or expired verification token", code="INVALID_TOKEN")
        await _redis_delete(f"email_verify:{token}")
        user = await self.users.get(UUID(user_id_raw))
        if user:
            user.email_verified_at = _now()

    async def send_otp(self, phone_number: str) -> None:
        user = await self.users.get_by_phone(phone_number)
        if not user:
            raise NotFoundError("Account not found for this phone number")
        otp = f"{secrets.randbelow(1000000):06d}"
        await _redis_setex(f"otp:{phone_number}", OTP_TTL_SECONDS, otp)
        await enqueue_sms(phone_number, f"Your verification code is {otp}")

    async def verify_otp(self, phone_number: str, otp: str) -> None:
        stored = await _redis_get(f"otp:{phone_number}")
        if not stored or stored != otp:
            raise UnauthorizedError("Invalid OTP", code="INVALID_OTP")
        await _redis_delete(f"otp:{phone_number}")
        user = await self.users.get_by_phone(phone_number)
        if user:
            user.phone_verified_at = _now()
