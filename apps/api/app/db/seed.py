from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.finance import seed_system_categories as _seed_system_categories


def seed_system_categories(session: Session) -> None:
    _seed_system_categories(session)
