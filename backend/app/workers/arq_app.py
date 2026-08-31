"""ARQ worker entrypoint.

Chosen over Celery: the codebase is fully async (asyncpg + async SQLAlchemy) and
ARQ is Redis-native, async-first and lightweight. Jobs share the same async app
code without bridges or serialization layers.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from arq.connections import RedisSettings

from app.config.settings import settings

logger = logging.getLogger("app.worker")

# arq (>=0.26) accepts a single startup/shutdown coroutine, not a list.
LifecycleHook = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class Settings:
    functions: list
    redis_settings: RedisSettings
    on_startup: LifecycleHook | None = None
    on_shutdown: LifecycleHook | None = None
    max_jobs: int = 10
    job_timeout: int = 300
    keep_result: int = 3600


def build_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.ARQ_REDIS_URL)


async def startup(ctx: dict) -> None:
    from app.db.session import build_engine

    ctx["engine"] = build_engine()
    logger.info("Worker started")


async def shutdown(ctx: dict) -> None:
    engine = ctx.get("engine")
    if engine:
        await engine.dispose()
    logger.info("Worker stopped")


def get_worker_settings() -> Settings:
    from app.workers import tasks

    return Settings(
        functions=[
            tasks.send_email,
            tasks.send_sms,
            tasks.send_push_notification,
            tasks.expire_subscriptions,
            tasks.expire_profile_shares,
            tasks.expire_job_verifications,
            tasks.cleanup_deleted_accounts,
            tasks.process_photo_thumbnail,
            tasks.process_payment_webhook,
            tasks.process_notification_campaign,
        ],
        redis_settings=build_redis_settings(),
        on_startup=startup,
        on_shutdown=shutdown,
    )


WorkerSettings = get_worker_settings()
