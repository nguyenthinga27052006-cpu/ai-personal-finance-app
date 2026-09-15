from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    return Path(__file__).resolve().parents[3]


REPOSITORY_ROOT = _find_repository_root()


class Settings(BaseSettings):
    app_name: str = "AI Personal Finance Assistant API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    database_url: str
    host_database_url: str | None = None
    redis_url: str
    log_level: str = "INFO"
    jwt_secret: str = "development-only-change-me-32-bytes-minimum"
    jwt_issuer: str = "ai-personal-finance-api"
    jwt_audience: str = "ai-personal-finance-mobile"
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=60)
    refresh_session_ttl_days: int = Field(default=30, ge=1, le=365)
    notification_worker_token: str = "development-worker-token"
    ai_provider: str = "fake"
    ai_model: str = "foundation-simple"
    ai_fallback_model: str = "foundation-fallback"
    ai_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    ai_enabled: bool = False
    ai_daily_budget_units: int = Field(default=100, ge=1)
    daily_user_token_limit: int = Field(default=50000, ge=1)
    ai_max_retries: int = Field(default=2, ge=0, le=5)
    release: str = "local"


    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        if self.app_env.lower() not in {"development", "test"}:
            if self.jwt_secret == "development-only-change-me-32-bytes-minimum":
                raise ValueError("JWT_SECRET must be configured outside development/test")
            if self.notification_worker_token == "development-worker-token":
                raise ValueError(
                    "NOTIFICATION_WORKER_TOKEN must be configured outside development/test"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_sqlalchemy_database_url() -> str:
    """Return a SQLAlchemy URL using the installed psycopg v3 driver."""
    url = get_settings().database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_sqlalchemy_migration_database_url() -> str:
    """Return the host database URL used by Alembic and host-side tools."""
    url = get_settings().host_database_url
    if not url:
        raise RuntimeError("HOST_DATABASE_URL must be configured for host-side migrations")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url
