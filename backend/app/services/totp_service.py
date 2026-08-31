"""TOTP two-factor authentication (RFC 6238), opt-in per user.

Secrets are stored in the ``user_totp_secrets`` table. Recovery codes are stored
as SHA-256 hashes only. Verification supports both a live TOTP code and a
single-use recovery code.
"""

import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

import pyotp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RecoveryCode, User, UserTotpSecret
from app.services.audit_service import AuditService

RECOVERY_CODE_COUNT = 8
RECOVERY_CODE_PREFIX = "MYT"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _generate_recovery_codes() -> list[str]:
    # Format: <prefix>-XXXX-XXXX (e.g. MYT-4F7K-9Q2M) — memorable and groupable.
    codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        a = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))
        b = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))
        codes.append(f"{RECOVERY_CODE_PREFIX}-{a}-{b}")
    return codes


class TotpService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit = AuditService(session)

    async def _get_secret(self, user_id: UUID) -> UserTotpSecret | None:
        return await self.session.scalar(select(UserTotpSecret).where(UserTotpSecret.user_id == user_id))

    async def is_enabled(self, user_id: UUID) -> bool:
        secret = await self._get_secret(user_id)
        return bool(secret and secret.is_enabled)

    async def setup(self, user: User) -> dict:
        """Generate (or rotate) a TOTP secret and issue fresh recovery codes."""
        existing = await self._get_secret(user.id)
        secret_b32 = pyotp.random_base32()
        if existing is None:
            existing = UserTotpSecret(user_id=user.id, secret=secret_b32, is_enabled=False)
            self.session.add(existing)
        else:
            existing.secret = secret_b32
            existing.is_enabled = False

        issuer = "Matchmaking Admin"
        otpauth_url = pyotp.totp.TOTP(secret_b32).provisioning_uri(name=user.email or str(user.id), issuer_name=issuer)

        # Replace the previous recovery codes (old ones are invalidated).
        recovery_codes = await self._replace_recovery_codes(user.id)

        await self.audit.record(action="totp.setup", actor_user_id=user.id, entity_type="user", entity_id=str(user.id))
        await self.session.flush()
        return {"secret": secret_b32, "otpauth_url": otpauth_url, "recovery_codes": recovery_codes}

    async def _replace_recovery_codes(self, user_id: UUID) -> list[str]:
        from sqlalchemy import delete

        await self.session.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user_id))
        codes = _generate_recovery_codes()
        for code in codes:
            self.session.add(RecoveryCode(user_id=user_id, code_hash=_hash_code(code.upper())))
        return codes

    async def enable(self, user: User, code: str) -> None:
        secret = await self._get_secret(user.id)
        if secret is None:
            from app.api.errors import ValidationAppError

            raise ValidationAppError("Run TOTP setup first", code="TOTP_NOT_SETUP")
        if not self._verify_code(secret.secret, code):
            from app.api.errors import UnauthorizedError

            raise UnauthorizedError("Invalid verification code", code="INVALID_TOTP")
        secret.is_enabled = True
        secret.last_used_at = datetime.now(UTC)
        await self.audit.record(
            action="totp.enabled", actor_user_id=user.id, entity_type="user", entity_id=str(user.id)
        )
        await self.session.flush()

    async def disable(self, user: User, password: str) -> None:
        from app.api.errors import UnauthorizedError
        from app.security.password import verify_password

        if not user.password_hash or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect", code="INVALID_PASSWORD")
        secret = await self._get_secret(user.id)
        if secret is None:
            return
        secret.is_enabled = False
        await self.audit.record(
            action="totp.disabled", actor_user_id=user.id, entity_type="user", entity_id=str(user.id)
        )
        await self.session.flush()

    async def admin_reset(self, admin: User, user_id: UUID) -> None:
        """Force-disable TOTP for a user (used by admin management)."""
        secret = await self._get_secret(user_id)
        if secret is not None:
            secret.is_enabled = False
        await self._replace_recovery_codes(user_id)
        await self.audit.record(
            action="admin.totp_reset",
            actor_user_id=admin.id,
            entity_type="user",
            entity_id=str(user_id),
        )
        await self.session.flush()

    async def verify(self, user: User, code: str) -> bool:
        """Accept either a valid TOTP code or an unused recovery code."""
        secret = await self._get_secret(user.id)
        if secret is None or not secret.is_enabled:
            return False

        if self._verify_code(secret.secret, code):
            secret.last_used_at = datetime.now(UTC)
            await self.session.flush()
            return True

        return await self._consume_recovery_code(user.id, code)

    async def _consume_recovery_code(self, user_id: UUID, code: str) -> bool:
        normalized = code.strip().upper()
        row = await self.session.scalar(
            select(RecoveryCode).where(
                RecoveryCode.user_id == user_id,
                RecoveryCode.code_hash == _hash_code(normalized),
                RecoveryCode.used_at.is_(None),
            )
        )
        if row is None:
            return False
        row.used_at = datetime.now(UTC)
        await self.session.flush()
        return True

    @staticmethod
    def _verify_code(secret_b32: str, code: str) -> bool:
        totp = pyotp.TOTP(secret_b32)
        return totp.verify(code.strip(), valid_window=1)
