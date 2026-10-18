import logging
from collections.abc import AsyncGenerator, Callable
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ForbiddenError, UnauthorizedError
from app.config.settings import settings
from app.db.models import User
from app.db.session import SessionLocal
from app.repositories.user_repo import UserRepository
from app.security.jwt import TokenError, decode_token
from app.security.rate_limit import check_rate_limit, client_key
from app.services.storage import StorageBackend, build_storage

logger = logging.getLogger("app.deps")

bearer_scheme = HTTPBearer(auto_error=False)

_active_roles = {"USER", "MODERATOR", "VERIFIER", "ADMIN", "SUPER_ADMIN"}


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated", code="NOT_AUTHENTICATED")
    try:
        payload = decode_token(credentials.credentials, "access")
    except TokenError as exc:
        raise UnauthorizedError(str(exc), code="INVALID_TOKEN") from exc
    user = await UserRepository(session).get(UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("Account not found", code="NOT_AUTHENTICATED")
    if user.deleted_at is not None or user.account_status.value == "DELETED":
        raise UnauthorizedError("Account deleted", code="ACCOUNT_DELETED")
    if user.is_banned or user.account_status.value == "BANNED":
        raise UnauthorizedError("Account banned", code="ACCOUNT_BANNED")
    return user


def require_role(*roles: str) -> Callable:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in roles:
            raise ForbiddenError("Insufficient permissions", code="FORBIDDEN")
        return user

    return dependency


def require_permission(*permissions: str) -> Callable:
    """Grants access only when the caller's role holds ALL the given permissions."""

    async def dependency(
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        from app.services.permission_service import PermissionService

        allowed = await PermissionService(session).permissions_for_role(user.role)
        if not all(p in allowed for p in permissions):
            raise ForbiddenError("Insufficient permissions", code="FORBIDDEN")
        return user

    return dependency


def require_any_permission(*permissions: str) -> Callable:
    """Grants access when the caller's role holds ANY of the given permissions."""

    async def dependency(
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        from app.services.permission_service import PermissionService

        allowed = await PermissionService(session).permissions_for_role(user.role)
        if not any(p in allowed for p in permissions):
            raise ForbiddenError("Insufficient permissions", code="FORBIDDEN")
        return user

    return dependency


async def get_storage() -> StorageBackend:
    return build_storage()


def rate_limit(bucket: str, key_func: Callable[[Request], str] | None = None):
    async def dependency(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
        key = key_func(request) if key_func else client_key(request)
        await check_rate_limit(key, bucket)
        return None

    return dependency


async def get_request_context(request: Request) -> dict:
    """Best-effort client IP for audit logging.

    ``X-Forwarded-For`` is only trusted when ``TRUSTED_PROXY_COUNT`` is set to
    the number of proxies in front of the app (e.g. 2 behind edge proxy + nginx).
    The client address is then read at that fixed offset from the right, where
    each trusted proxy appends the address it saw. With no trusted proxies the
    header is ignored entirely (it is spoofable by clients).
    """
    ip = request.client.host if request.client else None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and settings.TRUSTED_PROXY_COUNT > 0:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        index = len(parts) - settings.TRUSTED_PROXY_COUNT
        if 0 <= index < len(parts):
            ip = parts[index]
        elif parts:
            ip = parts[0]
    return {"ip": ip, "user_agent": request.headers.get("user-agent")}
