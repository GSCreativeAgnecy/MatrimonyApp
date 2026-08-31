from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_error_handlers
from app.api.v1 import api_router
from app.config.settings import settings
from app.security.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.config.logging import setup_logging

    setup_logging()
    yield
    await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Production-ready matrimony/matchmaking backend API",
    docs_url="/docs" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


# Local storage backend serves photo files during development.
if settings.STORAGE_BACKEND == "local":
    import os

    static_dir = os.path.abspath(settings.LOCAL_STORAGE_PATH)
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
