from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.models import User
from app.db.session import get_db
from app.insights.schemas import InsightListResponse, InsightResponse
from app.insights.service import InsightCandidate, active_insights

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])
DbSession = Annotated[Session, Depends(get_db)]


def _response(item: InsightCandidate) -> InsightResponse:
    return InsightResponse.model_validate(item.as_dict())


def _items(
    current_user: User,
    db: Session,
    start: date,
    end: date,
    currency: str | None,
    insight_type: str | None,
    severity: str | None,
) -> list[InsightResponse]:
    resolved_currency = (currency or current_user.default_currency).upper()
    items = active_insights(db, current_user, start, end, resolved_currency)
    if insight_type:
        items = [item for item in items if item.type == insight_type]
    if severity:
        items = [item for item in items if item.severity == severity.upper()]
    return [_response(item) for item in items]


@router.get("", response_model=InsightListResponse)
def list_active_insights(
    current_user: CurrentUser,
    db: DbSession,
    start: date = Query(...),
    end: date = Query(...),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    insight_type: str | None = Query(default=None, alias="type"),
    severity: str | None = Query(default=None),
) -> InsightListResponse:
    try:
        items = _items(current_user, db, start, end, currency, insight_type, severity)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail={"code": "invalid_insight_period", "message": str(exc)}
        ) from exc
    return InsightListResponse(items=items, total=len(items))


@router.get("/{insight_id}", response_model=InsightResponse)
def get_insight(
    insight_id: str,
    current_user: CurrentUser,
    db: DbSession,
    start: date = Query(...),
    end: date = Query(...),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
) -> InsightResponse:
    try:
        items = _items(current_user, db, start, end, currency, None, None)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail={"code": "invalid_insight_period", "message": str(exc)}
        ) from exc
    item = next((item for item in items if item.id == insight_id), None)
    if item is None:
        raise HTTPException(
            status_code=404, detail={"code": "insight_not_found", "message": "Insight not found"}
        )
    return item
