"""Fire-and-forget job enqueueing against ARQ. Fail-open so app is never blocked by the worker."""

import logging
from typing import Any

logger = logging.getLogger("app.enqueue")


async def enqueue_job(job_name: str, *args: Any, _defer_seconds: int | None = None) -> None:
    try:
        from arq.connections import ArqRedis, create_pool

        from app.workers.arq_app import build_redis_settings

        pool: ArqRedis = await create_pool(build_redis_settings())
        try:
            await pool.enqueue_job(job_name, *args, _defer_seconds=_defer_seconds)
        finally:
            await pool.aclose()
    except Exception:  # pragma: no cover - worker outage must not break API requests
        logger.warning("Failed to enqueue job %s (worker unavailable?)", job_name, exc_info=True)


async def enqueue_email(to: str, subject: str, html: str) -> None:
    await enqueue_job("send_email", to, subject, html)


async def enqueue_sms(to: str, body: str) -> None:
    await enqueue_job("send_sms", to, body)


async def enqueue_push(user_id: str, title: str, body: str, data: dict[str, Any] | None = None) -> None:
    await enqueue_job("send_push_notification", user_id, title, body, data)


async def enqueue_notification_campaign(campaign_id: str, defer_seconds: int | None = None) -> None:
    await enqueue_job("process_notification_campaign", campaign_id, _defer_seconds=defer_seconds)
