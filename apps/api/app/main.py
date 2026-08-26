from fastapi import FastAPI

from app.core.config import get_settings
from app.health import router as health_router

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(health_router)
