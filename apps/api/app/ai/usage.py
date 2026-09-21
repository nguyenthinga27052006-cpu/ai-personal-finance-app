from __future__ import annotations

import logging
from collections import defaultdict
from threading import Lock
from time import monotonic

logger = logging.getLogger("app.ai.usage")


class AIUsageLimitExceeded(Exception):
    def __init__(self, message: str, *, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class TokenLimitExceeded(AIUsageLimitExceeded):
    def __init__(
        self, message: str = "Daily token limit exceeded", *, retry_after: int = 86400
    ) -> None:
        super().__init__(message, retry_after=retry_after)
        self.code = "DAILY_TOKEN_LIMIT_EXCEEDED"


class InMemoryAIUsageBudget:
    """Local safety budget; production deployments must use shared storage."""

    def __init__(self, daily_units: int = 100, clock=monotonic) -> None:
        self.daily_units = daily_units
        self._clock = clock
        self._started_at = clock()
        self._usage: dict[tuple[str, str], int] = defaultdict(int)
        self._lock = Lock()

    def consume(self, user_id: str, feature: str, units: int = 1) -> int:
        if units < 1:
            raise ValueError("usage units must be positive")
        now = self._clock()
        with self._lock:
            if now - self._started_at >= 86_400:
                self._started_at = now
                self._usage.clear()
            key = (user_id, feature)
            total = self._usage[key] + units
            if total > self.daily_units:
                raise AIUsageLimitExceeded("AI usage budget exceeded", retry_after=86_400)
            self._usage[key] = total
            return total


class TokenBudgetTracker:
    """Tracks token consumption (prompt, completion, total) and enforces daily user token quotas."""

    def __init__(self, daily_limit: int = 50000, clock=monotonic) -> None:
        self.daily_limit = daily_limit
        self._clock = clock
        self._started_at = clock()
        self._token_usage: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def check_quota(self, user_id: str, estimated_tokens: int = 0) -> None:
        now = self._clock()
        with self._lock:
            if now - self._started_at >= 86_400:
                self._started_at = now
                self._token_usage.clear()
            current = self._token_usage[user_id]
            if current + estimated_tokens > self.daily_limit:
                raise TokenLimitExceeded(
                    f"Daily token limit of {self.daily_limit} exceeded (used: {current}, requested: {estimated_tokens})",
                    retry_after=86_400,
                )

    def record_usage(
        self,
        user_id: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> int:
        total = prompt_tokens + completion_tokens
        now = self._clock()
        with self._lock:
            if now - self._started_at >= 86_400:
                self._started_at = now
                self._token_usage.clear()
            self._token_usage[user_id] += total
            new_total = self._token_usage[user_id]

        # Safe structured JSON audit log without raw prompt or PII
        audit_payload = {
            "event": "token_budget_usage",
            "user_id": user_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total,
            "daily_total": new_total,
            "daily_limit": self.daily_limit,
        }
        logger.info("token_budget_audit %s", audit_payload)
        return new_total

    def get_user_usage(self, user_id: str) -> int:
        with self._lock:
            return self._token_usage.get(user_id, 0)

    def reset(self) -> None:
        with self._lock:
            self._started_at = self._clock()
            self._token_usage.clear()


_ai_usage_budget = InMemoryAIUsageBudget()
_token_budget_tracker = TokenBudgetTracker()


def get_ai_usage_budget() -> InMemoryAIUsageBudget:
    return _ai_usage_budget


def get_token_budget_tracker() -> TokenBudgetTracker:
    return _token_budget_tracker
