from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import jwt

from app.config.settings import settings

TokenType = Literal["access", "refresh", "mfa"]

MFA_TOKEN_EXPIRE_MINUTES = 5


class TokenError(Exception):
    """Raised when a token is invalid/expired/revoked."""


def _create_token(subject: str, token_type: TokenType, *, expires: timedelta, jti: str | None = None) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
        "jti": jti or str(uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str) -> str:
    return _create_token(subject, "access", expires=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at)."""
    jti = str(uuid4())
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expires_at = datetime.now(UTC) + expires
    return _create_token(subject, "refresh", expires=expires, jti=jti), jti, expires_at


def create_mfa_token(subject: str) -> str:
    """Short-lived token minted between password login and TOTP verification."""
    return _create_token(subject, "mfa", expires=timedelta(minutes=MFA_TOKEN_EXPIRE_MINUTES))


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "jti", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc
    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")
    return payload
