from __future__ import annotations

import logging
from collections.abc import Mapping
from types import TracebackType
from typing import Any

logger = logging.getLogger("app.error_tracking")

_SENSITIVE_KEYS = {
    "password",
    "passphrase",
    "secret",
    "token",
    "jwt",
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "client_secret",
    "private_key",
    "cookie",
}


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return normalized in _SENSITIVE_KEYS or normalized.endswith(
        ("_key", "_token", "_secret", "_password")
    )


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return sanitize_context(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_value(item) for item in value)
    return value


def sanitize_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in context.items():
        if _is_sensitive_key(key):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            sanitized[key] = sanitize_context(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_context(item) if isinstance(item, Mapping) else sanitize_value(item)
                for item in value
            ]
        elif isinstance(value, tuple):
            sanitized[key] = tuple(
                sanitize_context(item) if isinstance(item, Mapping) else sanitize_value(item)
                for item in value
            )
        else:
            sanitized[key] = sanitize_value(value)
    return sanitized


class LocalErrorTracker:
    def __init__(self, *, release: str = "local", environment: str = "local") -> None:
        self.release = release
        self.environment = environment

    def capture_exception(
        self,
        exc: Exception,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        traceback: TracebackType | None = None,
    ) -> dict[str, Any]:
        payload = {
            "type": exc.__class__.__name__,
            "message": str(exc),
            "release": self.release,
            "environment": self.environment,
            "request_id": request_id or "-",
            "trace_id": trace_id or "-",
            "context": sanitize_context(context),
        }
        logger.error(
            "captured_exception",
            exc_info=(type(exc), exc, traceback or exc.__traceback__),
            extra={"error_event": {**payload, "message": "[OMITTED_FROM_LOG]"}},
        )
        return payload
