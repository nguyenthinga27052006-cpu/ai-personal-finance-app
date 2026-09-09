from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.dashboard.schemas import DashboardResponse
from app.dashboard.service import build_dashboard
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=DashboardResponse)
def dashboard(current_user: CurrentUser, db: DbSession) -> DashboardResponse:
    return DashboardResponse.model_validate(build_dashboard(db, current_user))
