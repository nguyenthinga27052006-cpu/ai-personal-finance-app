from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock
from time import monotonic
from typing import Protocol


class AuthRateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...


class InMemoryAuthRateLimiter:
    def __init__(
        self,
        max_attempts: int = 10,
        window_seconds: int = 60,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            attempts = self._attempts[key]
            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.max_attempts:
                return False
            attempts.append(now)
            return True


_auth_rate_limiter: AuthRateLimiter = InMemoryAuthRateLimiter()
_ai_rate_limiter: AuthRateLimiter = InMemoryAuthRateLimiter(max_attempts=30, window_seconds=60)


def get_auth_rate_limiter() -> AuthRateLimiter:
    return _auth_rate_limiter


def get_ai_rate_limiter() -> AuthRateLimiter:
    return _ai_rate_limiter
