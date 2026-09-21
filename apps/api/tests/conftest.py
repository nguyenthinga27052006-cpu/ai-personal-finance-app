from __future__ import annotations

import os
from pathlib import Path


def _load_repository_environment() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    environment_file = repository_root / ".env"
    if not environment_file.is_file():
        return

    for raw_line in environment_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if name.strip() == "POSTGRES_TEST_DATABASE_URL" and value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+psycopg://", 1)
        os.environ.setdefault(name.strip(), value)


_load_repository_environment()


import pytest  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db.base import Base  # noqa: E402


@pytest.fixture
def db_session():
    engine = sa.create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    with factory() as session:
        yield session
    engine.dispose()
