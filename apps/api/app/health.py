import psycopg
from fastapi import APIRouter, HTTPException, status
from redis import Redis

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    settings = get_settings()
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as connection:
            connection.execute("SELECT 1")
        Redis.from_url(settings.redis_url, socket_connect_timeout=3).ping()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="dependencies are not ready",
        ) from exc

    return {"status": "ready"}
