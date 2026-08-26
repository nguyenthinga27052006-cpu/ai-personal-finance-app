from app.core.config import (
    REPOSITORY_ROOT,
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
