from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.budget_goals.schemas import (
    BudgetCategoryCreate,
    BudgetCreate,
    BudgetResponse,
    BudgetStatusResponse,
    BudgetUpdate,
    ContributionCreate,
    ContributionResponse,
    GoalCreate,
    GoalResponse,
    GoalStatusResponse,
    GoalUpdate,
)
from app.budget_goals.service import (
    BudgetGoalError,
    ResourceNotFound,
    _budget,
    _goal,
    budget_calculation,
    create_budget,
    create_contribution,
    create_goal,
    delete_budget,
    effective_expenses,
    goal_calculation,
    list_budgets,
    list_contributions,
    list_goals,
    update_budget,
)
from app.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["budgets", "goals"])
DbSession = Annotated[Session, Depends(get_db)]


def error(exc: BudgetGoalError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND
        if isinstance(exc, ResourceNotFound)
        else status.HTTP_400_BAD_REQUEST,
        detail={"code": "budget_goal_error", "message": str(exc) or "Resource not found"},
    )


def budget_response(db: Session, user, budget) -> BudgetResponse:
    expenses = effective_expenses(db, user, budget.start_date, budget.end_date, budget.currency)
    categories = []
    for item in budget.categories:
        spent = expenses.get(item.category_id, 0)
        utilization = spent / item.limit_amount
        categories.append(
            {
                **item.__dict__,
                "spent": spent,
                "remaining": item.limit_amount - spent,
                "utilization": utilization,
                "risk": "OVER"
                if utilization >= 1
                else "DANGER"
                if utilization >= 0.9
                else "WARNING"
                if utilization >= 0.8
                else "SAFE",
            }
        )
    return BudgetResponse.model_validate(
        {
            **budget.__dict__,
            "categories": categories,
            "calculation": budget_calculation(db, user, budget),
        }
    )


def goal_response(goal) -> GoalResponse:
    return GoalResponse.model_validate(
        {
            **goal.__dict__,
            "contributions": goal.contributions,
            "calculation": goal_calculation(goal),
        }
    )


@router.get("/budgets", response_model=list[BudgetResponse])
def budgets(current_user: CurrentUser, db: DbSession) -> list[BudgetResponse]:
    return [budget_response(db, current_user, item) for item in list_budgets(db, current_user)]


@router.post("/budgets", response_model=BudgetResponse, status_code=201)
def create_budget_route(
    payload: BudgetCreate, current_user: CurrentUser, db: DbSession
) -> BudgetResponse:
    try:
        budget = create_budget(db, current_user, payload.model_dump())
        db.commit()
        db.refresh(budget)
        return budget_response(db, current_user, budget)
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
def get_budget(budget_id: str, current_user: CurrentUser, db: DbSession) -> BudgetResponse:
    try:
        return budget_response(db, current_user, _budget(db, current_user, budget_id))
    except BudgetGoalError as exc:
        raise error(exc) from exc


@router.get("/budgets/{budget_id}/status", response_model=BudgetStatusResponse)
def budget_status(budget_id: str, current_user: CurrentUser, db: DbSession) -> BudgetStatusResponse:
    try:
        return BudgetStatusResponse.model_validate(
            budget_calculation(db, current_user, _budget(db, current_user, budget_id))
        )
    except BudgetGoalError as exc:
        raise error(exc) from exc


@router.patch("/budgets/{budget_id}", response_model=BudgetResponse)
def patch_budget(
    budget_id: str, payload: BudgetUpdate, current_user: CurrentUser, db: DbSession
) -> BudgetResponse:
    try:
        budget = update_budget(db, current_user, budget_id, payload.model_dump(exclude_unset=True))
        db.commit()
        return budget_response(db, current_user, budget)
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.delete("/budgets/{budget_id}", status_code=204)
def remove_budget(budget_id: str, current_user: CurrentUser, db: DbSession) -> None:
    try:
        delete_budget(db, current_user, budget_id)
        db.commit()
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.post("/budgets/{budget_id}/categories", response_model=BudgetResponse)
def add_budget_category(
    budget_id: str, payload: BudgetCategoryCreate, current_user: CurrentUser, db: DbSession
) -> BudgetResponse:
    try:
        budget = _budget(db, current_user, budget_id)
        from app.budget_goals.service import _add_categories

        _add_categories(db, current_user, budget, [payload.model_dump()])
        db.commit()
        return budget_response(db, current_user, budget)
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.get("/goals", response_model=list[GoalResponse])
def goals(current_user: CurrentUser, db: DbSession) -> list[GoalResponse]:
    return [goal_response(item) for item in list_goals(db, current_user)]


@router.post("/goals", response_model=GoalResponse, status_code=201)
def create_goal_route(
    payload: GoalCreate, current_user: CurrentUser, db: DbSession
) -> GoalResponse:
    goal = create_goal(db, current_user, payload.model_dump())
    db.commit()
    db.refresh(goal)
    return goal_response(goal)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: str, current_user: CurrentUser, db: DbSession) -> GoalResponse:
    try:
        return goal_response(_goal(db, current_user, goal_id))
    except BudgetGoalError as exc:
        raise error(exc) from exc


@router.get("/goals/{goal_id}/status", response_model=GoalStatusResponse)
def goal_status(goal_id: str, current_user: CurrentUser, db: DbSession) -> GoalStatusResponse:
    try:
        return GoalStatusResponse.model_validate(goal_calculation(_goal(db, current_user, goal_id)))
    except BudgetGoalError as exc:
        raise error(exc) from exc


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
def patch_goal(
    goal_id: str, payload: GoalUpdate, current_user: CurrentUser, db: DbSession
) -> GoalResponse:
    try:
        goal = _goal(db, current_user, goal_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(goal, key, value)
        db.commit()
        return goal_response(goal)
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.delete("/goals/{goal_id}", status_code=204)
def remove_goal(goal_id: str, current_user: CurrentUser, db: DbSession) -> None:
    try:
        db.delete(_goal(db, current_user, goal_id))
        db.commit()
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.post("/goals/{goal_id}/contributions", response_model=ContributionResponse, status_code=201)
def contribution(
    goal_id: str, payload: ContributionCreate, current_user: CurrentUser, db: DbSession
) -> ContributionResponse:
    try:
        item = create_contribution(db, current_user, goal_id, payload.model_dump(exclude_none=True))
        db.commit()
        db.refresh(item)
        return item
    except BudgetGoalError as exc:
        db.rollback()
        raise error(exc) from exc


@router.get("/goals/{goal_id}/contributions", response_model=list[ContributionResponse])
def contributions(
    goal_id: str, current_user: CurrentUser, db: DbSession
) -> list[ContributionResponse]:
    try:
        return list_contributions(db, current_user, goal_id)
    except BudgetGoalError as exc:
        raise error(exc) from exc
