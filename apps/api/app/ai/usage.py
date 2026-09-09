from __future__ import annotations

from collections import defaultdict
from threading import Lock
from time import monotonic


class AIUsageLimitExceeded(Exception):
    def __init__(self, message: str, *, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


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


_ai_usage_budget = InMemoryAIUsageBudget()


def get_ai_usage_budget() -> InMemoryAIUsageBudget:
    return _ai_usage_budget
