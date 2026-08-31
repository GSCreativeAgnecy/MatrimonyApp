from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.config.settings import settings
from app.db.base import Base
from app.db.models import all_models  # noqa: F401  (populates metadata)
from app.main import app

settings.RATE_LIMIT_ENABLED = False
settings.DEBUG = False
settings.STORAGE_BACKEND = "local"
settings.LOCAL_STORAGE_PATH = "./storage_test"
# Point Redis at a closed port with a short timeout so "unavailable" paths fail fast.
settings.REDIS_URL = "redis://127.0.0.1:6399/0?socket_connect_timeout=0.3&socket_timeout=0.3"


@pytest.fixture(scope="session", autouse=True)
def fast_argon2():
    """Use a low-cost Argon2 hasher so auth tests run quickly."""
    from argon2 import PasswordHasher

    import app.security.password as pw

    pw._hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)


@pytest.fixture(scope="session", autouse=True)
def no_enqueue():
    """Never contact the worker/Redis from tests; enqueueing becomes a no-op."""
    import app.workers.enqueue as enqueue_mod

    async def _noop(*args, **kwargs) -> None:
        return None

    enqueue_mod.enqueue_job = _noop


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def override_get_session(session_factory):
    async def _override() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(override_get_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


def unique_email(name: str = "user") -> str:
    import uuid

    return f"{name}-{uuid.uuid4().hex[:8]}@example.com"


async def register_user(client: AsyncClient, *, email: str | None = None, password: str = "Testpass123") -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email or unique_email(), "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def login_user(client: AsyncClient, email: str, password: str = "Testpass123") -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def create_full_profile(client: AsyncClient, tokens: dict, gender: str = "FEMALE") -> dict:
    resp = await client.post(
        "/api/v1/profile",
        headers=auth_headers(tokens),
        json={
            "first_name": "Anita",
            "gender": gender,
            "date_of_birth": "1994-06-15",
            "religion": "Hindu",
            "caste": "Brahmin",
            "mother_tongue": "Hindi",
            "education": "B.Tech",
            "occupation": "Engineer",
            "city": "Mumbai",
            "country": "India",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]
