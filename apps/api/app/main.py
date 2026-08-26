from fastapi import FastAPI

from app.auth.routes import me_router
from app.auth.routes import router as auth_router
from app.core.config import get_settings
from app.health import router as health_router

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(me_router)
