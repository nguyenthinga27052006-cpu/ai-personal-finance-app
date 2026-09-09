from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.accounts.service import list_accounts
from app.ai.context import ExecutionContext, Provenance
from app.ai.errors import (
    AuthenticationContextError,
    AuthorizationError,
    InsufficientDataError,
    ToolExecutionError,
    ToolNotAllowedError,
    WriteToolsDisabledError,
)
from app.ai.guardrails import validate_tool_arguments
from app.analytics.service import build_overview
from app.budget_goals.service import budget_calculation, goal_calculation, list_budgets, list_goals
from app.insights.service import active_insights
from app.transactions.service import list_transactions


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PeriodInput(ToolInput):
    start: date
    end: date
    currency: str = Field(min_length=3, max_length=3)

    def validate_period(self) -> None:
        if self.end < self.start or self.end - self.start > timedelta(days=365):
            raise ValueError("Tool period must be between 0 and 366 days")


class CurrencyInput(ToolInput):
    currency: str = Field(min_length=3, max_length=3)


class BudgetInput(PeriodInput):
    budget_id: str | None = None


class RecentTransactionsInput(CurrencyInput):
    limit: int = Field(default=10, ge=1, le=10)


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    data: dict[str, Any]
    provenance: list[Provenance]


ToolHandler = Callable[[ExecutionContext, ToolInput], ToolResult]
T = TypeVar("T", bound=ToolInput)


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[ToolInput],
        handler: ToolHandler,
        *,
        capability: str = "READ",
        authorization: str = "authenticated_user",
    ) -> None:
        self.name = name
        self.description = description
        self.input_model = input_model
        self.handler = handler
        self.capability = capability
        self.authorization = authorization


def _period_provenance(source: str, payload: PeriodInput) -> list[Provenance]:
    return [
        Provenance(
            source=source,
            period_start=payload.start,
            period_end=payload.end,
            calculation_type="canonical_service",
        )
    ]


def _current_balance(context: ExecutionContext, payload: CurrencyInput) -> ToolResult:
    accounts = list_accounts(context.db, context.user)
    rows = [
        {"id": account.id, "name": account.name, "balance": account.current_balance}
        for account in accounts
        if account.currency == payload.currency.upper()
    ]
    return ToolResult(
        tool="get_current_balance",
        data={
            "currency": payload.currency.upper(),
            "total": sum(row["balance"] for row in rows),
            "accounts": rows,
        },
        provenance=[
            Provenance(source="accounts.service", calculation_type="account_balance_cache")
        ],
    )


def _overview_tool(name: str, context: ExecutionContext, payload: PeriodInput) -> ToolResult:
    payload.validate_period()
    overview = build_overview(
        context.db, context.user, payload.start, payload.end, payload.currency.upper()
    )
    if not overview["summary"]["records"]:
        raise InsufficientDataError("No canonical financial facts are available for this period")
    if name == "get_monthly_income":
        data = {"currency": payload.currency.upper(), "income": overview["summary"]["income"]}
    elif name == "get_monthly_expense":
        data = {"currency": payload.currency.upper(), "expense": overview["summary"]["expense"]}
    elif name == "get_category_spending":
        data = {"categories": overview["category_analysis"][:10]}
    elif name == "get_spending_trend":
        data = {"monthly": overview["time_analysis"]["monthly"][-12:]}
    else:
        data = {"overview": overview}
    return ToolResult(
        tool=name,
        data=data,
        provenance=_period_provenance("analytics.service", payload),
    )


def _budget_status(context: ExecutionContext, payload: BudgetInput) -> ToolResult:
    payload.validate_period()
    budgets = list_budgets(context.db, context.user)
    selected = [
        budget
        for budget in budgets
        if budget.currency == payload.currency.upper()
        and (payload.budget_id is None or budget.id == payload.budget_id)
        and budget.end_date >= payload.start
        and budget.start_date <= payload.end
    ]
    return ToolResult(
        tool="get_budget_status",
        data={
            "budgets": [
                {
                    "id": budget.id,
                    "name": budget.name,
                    "status": budget_calculation(context.db, context.user, budget),
                }
                for budget in selected
            ]
        },
        provenance=_period_provenance("budget_goals.service", payload),
    )


def _goal_progress(context: ExecutionContext, payload: PeriodInput) -> ToolResult:
    payload.validate_period()
    goals = [
        goal
        for goal in list_goals(context.db, context.user)
        if goal.currency == payload.currency.upper()
    ]
    return ToolResult(
        tool="get_goal_progress",
        data={
            "goals": [
                {"id": goal.id, "name": goal.name, "status": goal_calculation(goal, payload.end)}
                for goal in goals
            ]
        },
        provenance=_period_provenance("budget_goals.service", payload),
    )


def _recent_transactions(context: ExecutionContext, payload: RecentTransactionsInput) -> ToolResult:
    rows, _ = list_transactions(context.db, context.user, 1, payload.limit, None, None)
    records = [
        {
            "id": item.id,
            "type": item.type,
            "amount": item.amount,
            "currency": item.currency,
            "date": item.transaction_date,
            "description": item.description,
        }
        for item in rows
        if item.currency == payload.currency.upper()
    ]
    return ToolResult(
        tool="get_recent_transactions",
        data={"transactions": records},
        provenance=[
            Provenance(source="transactions.service", calculation_type="owned_recent_records")
        ],
    )


def _insights(context: ExecutionContext, payload: PeriodInput) -> ToolResult:
    payload.validate_period()
    items = active_insights(
        context.db, context.user, payload.start, payload.end, payload.currency.upper()
    )
    return ToolResult(
        tool="get_insights",
        data={"items": [item.as_dict() for item in items[:10]]},
        provenance=_period_provenance("insights.service", payload),
    )


class ToolRegistry:
    def __init__(self, definitions: list[ToolDefinition]) -> None:
        self._definitions = {definition.name: definition for definition in definitions}

    def list(self) -> list[ToolDefinition]:
        return list(self._definitions.values())

    def get(self, name: str) -> ToolDefinition:
        try:
            return self._definitions[name]
        except KeyError as exc:
            raise ToolNotAllowedError(f"Tool is not registered: {name}") from exc

    def execute(
        self, name: str, context: ExecutionContext, arguments: dict[str, Any]
    ) -> ToolResult:
        context.require_authenticated()
        validate_tool_arguments(arguments)
        definition = self.get(name)
        if name not in context.allowed_tools:
            raise AuthorizationError("Tool is not allowed for this feature")
        if definition.capability != "READ":
            raise WriteToolsDisabledError("Write tools are not production-enabled")
        try:
            payload = definition.input_model.model_validate(arguments)
            return definition.handler(context, payload)
        except (AuthenticationContextError, AuthorizationError, InsufficientDataError):
            raise
        except Exception as exc:
            raise ToolExecutionError(f"Tool execution failed: {name}") from exc


def build_read_only_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            ToolDefinition(
                "get_current_balance", "Get owned account balances", CurrencyInput, _current_balance
            ),
            ToolDefinition(
                "get_monthly_income",
                "Get canonical period income",
                PeriodInput,
                lambda c, p: _overview_tool("get_monthly_income", c, p),
            ),
            ToolDefinition(
                "get_monthly_expense",
                "Get canonical period expense",
                PeriodInput,
                lambda c, p: _overview_tool("get_monthly_expense", c, p),
            ),
            ToolDefinition(
                "get_category_spending",
                "Get canonical category spending",
                PeriodInput,
                lambda c, p: _overview_tool("get_category_spending", c, p),
            ),
            ToolDefinition(
                "get_spending_trend",
                "Get canonical spending trend",
                PeriodInput,
                lambda c, p: _overview_tool("get_spending_trend", c, p),
            ),
            ToolDefinition(
                "get_budget_status", "Get owned budget calculations", BudgetInput, _budget_status
            ),
            ToolDefinition(
                "get_goal_progress", "Get owned goal calculations", PeriodInput, _goal_progress
            ),
            ToolDefinition(
                "get_recent_transactions",
                "Get a bounded owned transaction list",
                RecentTransactionsInput,
                _recent_transactions,
            ),
            ToolDefinition(
                "get_insights", "Get deterministic owned insights", PeriodInput, _insights
            ),
        ]
    )


class WriteTool:
    capability = "WRITE"

    def execute(self, *_: Any, **__: Any) -> None:
        raise WriteToolsDisabledError("Write tools are abstraction-only in Phase 13")
