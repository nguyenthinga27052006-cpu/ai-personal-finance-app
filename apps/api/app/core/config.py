from functools import lru_cache
from pathlib import Path

from pydantic import Field
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

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


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
