from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-me-in-production"
_DEFAULT_WEBHOOK_SECRET = "change-me-webhook-secret"
_ALLOWED_PAYMENT_PROVIDERS = {"mock", "stripe"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "Matchmaking API"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://matchmake:matchmake@localhost:5432/matchmaking"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test_matchmaking.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Storage
    STORAGE_BACKEND: str = "local"  # local | s3
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str = "matchmaking-dev"
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_REGION: str = "us-east-1"
    S3_UPLOAD_URL_EXPIRES: int = 3600
    S3_DOWNLOAD_URL_EXPIRES: int = 3600
    LOCAL_STORAGE_PATH: str = "./storage"

    # Payments
    PAYMENT_PROVIDER: str = "mock"  # mock | stripe
    PAYMENT_API_KEY: str | None = None
    PAYMENT_WEBHOOK_SECRET: str = _DEFAULT_WEBHOOK_SECRET
    # Escape hatch for demo/staging deployments that intentionally run the mock
    # provider with ENVIRONMENT=production. Never enable in a real production.
    ALLOW_MOCK_PAYMENTS: bool = False

    # Email / SMS
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@matchmaking.local"
    SMS_PROVIDER: str = "mock"
    SMS_API_KEY: str | None = None

    # Security / limits
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: str = "10/15m"
    OTP_RATE_LIMIT: str = "5/15m"
    MAX_PHOTO_SIZE_MB: int = 10
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    TRUSTED_PROXY_COUNT: int = 0

    # Worker
    ARQ_REDIS_URL: str = "redis://localhost:6379/1"
    # Set false for local development without Redis/worker: background jobs are
    # skipped instead of retrying (which adds ~10s to requests). Production keeps
    # jobs enabled; enqueueing is fail-open either way.
    ENQUEUE_JOBS: bool = True

    # Lookups / pricing config
    LOCAL_JOB_VERIFICATION_PRICE: int = 119
    NRI_JOB_VERIFICATION_PRICE: int = 199
    JOB_VERIFICATION_CURRENCY: str = "INR"

    # Remote app configuration cache
    APP_CONFIG_CACHE_TTL: int = 900
    APP_CONFIG_CACHE_KEY: str = "app_config:public"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _default_scheme(cls, v: str) -> str:
        return v

    @field_validator("PAYMENT_PROVIDER")
    @classmethod
    def _known_payment_provider(cls, v: str) -> str:
        provider = (v or "").strip().lower()
        if provider not in _ALLOWED_PAYMENT_PROVIDERS:
            raise ValueError(f"PAYMENT_PROVIDER must be one of {sorted(_ALLOWED_PAYMENT_PROVIDERS)}, got {v!r}")
        return provider

    @model_validator(mode="after")
    def _production_safety(self) -> "Settings":
        """Fail fast on insecure production configuration instead of booting unsafely."""
        if not self.is_production:
            return self

        errors: list[str] = []
        if self.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET or len(self.JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY must be set to a random value of at least 32 characters in production")
        if self.PAYMENT_PROVIDER == "mock" and not self.ALLOW_MOCK_PAYMENTS:
            errors.append(
                "PAYMENT_PROVIDER=mock is not allowed in production (the mock provider accepts webhooks "
                "without a real payment). Set PAYMENT_PROVIDER to a real provider, or explicitly set "
                "ALLOW_MOCK_PAYMENTS=true for a demo deployment."
            )
        if self.PAYMENT_PROVIDER == "stripe":
            if not self.PAYMENT_API_KEY:
                errors.append("PAYMENT_API_KEY is required when PAYMENT_PROVIDER=stripe")
            if self.PAYMENT_WEBHOOK_SECRET in {_DEFAULT_WEBHOOK_SECRET, ""}:
                errors.append("PAYMENT_WEBHOOK_SECRET must be set when PAYMENT_PROVIDER=stripe")
        if errors:
            raise ValueError("Insecure production configuration: " + "; ".join(errors))
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
