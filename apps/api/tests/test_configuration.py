from app.core.config import (
    REPOSITORY_ROOT,
    Settings,
    get_settings,
    get_sqlalchemy_database_url,
    get_sqlalchemy_migration_database_url,
)


def test_database_urls_keep_host_and_docker_contexts_separate(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("HOST_DATABASE_URL", raising=False)
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.database_url.endswith("@postgres:5432/finance")
    assert settings.host_database_url is not None
    assert settings.host_database_url.endswith("@localhost:5433/finance")
    assert get_sqlalchemy_database_url().endswith("@postgres:5432/finance")
    assert get_sqlalchemy_migration_database_url().endswith("@localhost:5433/finance")


def test_settings_loads_the_repository_root_environment_file() -> None:
    assert REPOSITORY_ROOT == REPOSITORY_ROOT.resolve()
    assert (REPOSITORY_ROOT / ".env").is_file()
    assert get_settings().database_url


def test_non_development_settings_reject_default_security_tokens() -> None:
    values = {
        "app_env": "production",
        "database_url": "postgresql://db/finance",
        "redis_url": "redis://redis:6379/0",
        "jwt_secret": "development-only-change-me-32-bytes-minimum",
        "notification_worker_token": "worker-token",
    }
    try:
        Settings(**values)
    except ValueError as exc:
        assert "JWT_SECRET" in str(exc)
    else:  # pragma: no cover - assertion documents the security invariant
        raise AssertionError("production settings accepted the development JWT secret")

    values["jwt_secret"] = "configured-production-secret"
    values["notification_worker_token"] = "development-worker-token"
    try:
        Settings(**values)
    except ValueError as exc:
        assert "NOTIFICATION_WORKER_TOKEN" in str(exc)
    else:  # pragma: no cover - assertion documents the security invariant
        raise AssertionError("production settings accepted the development worker token")
