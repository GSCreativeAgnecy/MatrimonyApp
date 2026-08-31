from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings


def build_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.DATABASE_URL
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_async_engine(
        url,
        echo=settings.DEBUG and "sqlite" not in url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args=connect_args,
    )


engine: AsyncEngine = build_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables directly (used ONLY for tests / local demo, not production)."""
    from app.db.models import all_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(all_models.metadata.create_all)
