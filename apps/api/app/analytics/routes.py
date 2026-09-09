from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsOverviewResponse
from app.analytics.service import build_overview
from app.auth.dependencies import CurrentUser
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def overview(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    start: date = Query(...),
    end: date = Query(...),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    budget_id: str | None = Query(default=None),
) -> AnalyticsOverviewResponse:
    resolved_currency = (currency or current_user.default_currency).upper()
    try:
        return build_overview(db, current_user, start, end, resolved_currency, budget_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail={"code": "invalid_analytics_period", "message": str(exc)}
        ) from exc
