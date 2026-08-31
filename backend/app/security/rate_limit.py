"""Sliding-window rate limiter backed by Redis.

Usage: `bucket = parse_limit("10/15m")` gives 10 requests per 15 minutes.
"""

import time
from dataclasses import dataclass

from fastapi import HTTPException, Request
from fastapi import status as http_status

from app.config.settings import settings
from app.security.redis import get_redis

LIMIT_PATTERNS: dict[str, str] = {
    "login": settings.LOGIN_RATE_LIMIT,
    "otp": settings.OTP_RATE_LIMIT,
}


@dataclass(frozen=True)
class RateLimit:
    limit: int
    window_seconds: int


def parse_limit(spec: str) -> RateLimit:
    count, _, window = spec.partition("/")
    seconds = {"m": 60, "h": 3600, "d": 86400}[window[-1]]
    return RateLimit(limit=int(count), window_seconds=int(window[:-1]) * seconds)


async def check_rate_limit(key: str, bucket: str) -> None:
    """Raises 429 when the caller exceeds the limit for `bucket`."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    rl = parse_limit(LIMIT_PATTERNS.get(bucket, "100/15m"))
    redis = await get_redis()
    now = int(time.time())
    window_start = now - now % rl.window_seconds
    redis_key = f"rl:{bucket}:{key}:{window_start}"
    try:
        count = await redis.incr(redis_key)
        if count == 1:
            await redis.expire(redis_key, rl.window_seconds)
    except Exception:  # fail-open so Redis outages never lock users out
        return
    if count > rl.limit:
        raise HTTPException(
            status_code=http_status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests. Please try again later."},
        )


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
