from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.models import Recommendation, RecommendationEvent
from app.db.session import get_db
from app.recommendations.schemas import (
    RecommendationEventResponse,
    RecommendationFeedbackRequest,
    RecommendationListResponse,
    RecommendationResponse,
)
from app.recommendations.service import (
    ACCEPTED,
    DISMISSED,
    active_recommendations,
    add_feedback,
    transition,
)

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])
DbSession = Annotated[Session, Depends(get_db)]


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "recommendation_not_found", "message": "Recommendation not found"},
    )


@router.get("", response_model=RecommendationListResponse)
def list_recommendations(
    current_user: CurrentUser,
    db: DbSession,
    start: date = Query(...),
    end: date = Query(...),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
) -> RecommendationListResponse:
    if end < start:
        raise HTTPException(status_code=422, detail={"code": "invalid_recommendation_period"})
    items = active_recommendations(
        db, current_user, start, end, (currency or current_user.default_currency).upper()
    )
    db.commit()
    return RecommendationListResponse(items=items, total=len(items))


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation(
    recommendation_id: str,
    current_user: CurrentUser,
    db: DbSession,
    start: date = Query(...),
    end: date = Query(...),
    currency: str | None = Query(default=None, min_length=3, max_length=3),
) -> RecommendationResponse:
    items = active_recommendations(
        db, current_user, start, end, (currency or current_user.default_currency).upper()
    )
    item = next((candidate for candidate in items if candidate.id == recommendation_id), None)
    if item is None:
        raise _not_found()
    db.commit()
    return item


@router.post("/{recommendation_id}/accept", response_model=RecommendationResponse)
def accept_recommendation(
    recommendation_id: str, current_user: CurrentUser, db: DbSession
) -> RecommendationResponse:
    item = transition(db, current_user, recommendation_id, ACCEPTED)
    if item is None:
        raise _not_found()
    db.commit()
    db.refresh(item)
    return item


@router.post("/{recommendation_id}/dismiss", response_model=RecommendationResponse)
def dismiss_recommendation(
    recommendation_id: str, current_user: CurrentUser, db: DbSession
) -> RecommendationResponse:
    item = transition(db, current_user, recommendation_id, DISMISSED)
    if item is None:
        raise _not_found()
    db.commit()
    db.refresh(item)
    return item


@router.post("/{recommendation_id}/feedback", response_model=RecommendationResponse)
def feedback_recommendation(
    recommendation_id: str,
    payload: RecommendationFeedbackRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> RecommendationResponse:
    item = add_feedback(db, current_user, recommendation_id, payload.feedback, payload.metadata)
    if item is None:
        raise _not_found()
    db.commit()
    db.refresh(item)
    return item


@router.post(
    "/{recommendation_id}/events", response_model=RecommendationEventResponse, status_code=201
)
def record_recommendation_event(
    recommendation_id: str,
    current_user: CurrentUser,
    db: DbSession,
    event_type: str = Query(..., pattern="^(SHOWN|ACTION_OUTCOME)$"),
) -> RecommendationEventResponse:
    item = db.scalar(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == current_user.id,
        )
    )
    if item is None:
        raise _not_found()
    event = RecommendationEvent(
        recommendation_id=item.id,
        user_id=current_user.id,
        event_type=event_type,
        metadata_json={"financial_write": False},
    )
    db.add(event)
    db.commit()
    return RecommendationEventResponse(id=event.id, status="recorded")


@router.post("/internal/evaluate", include_in_schema=False)
def evaluate_recommendation_cycle(
    db: DbSession, x_worker_token: str | None = Header(default=None, alias="X-Worker-Token")
) -> int:
    from app.core.config import get_settings
    from app.recommendations.service import evaluate_all_users

    if x_worker_token != get_settings().notification_worker_token:
        raise HTTPException(status_code=401, detail={"code": "invalid_worker_token"})
    return evaluate_all_users(db)
