from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from app.ai.errors import GuardrailViolation

_INJECTION_PATTERNS = (
    "ignore previous",
    "ignore all instructions",
    "reveal system prompt",
    "show system prompt",
    "change authenticated user",
    "use another user",
    "bypass authorization",
    "give me the secret",
)
_SECRET_PATTERNS = (
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "authorization",
    "jwt_secret",
    "password",
)
_SQL_PATTERN = re.compile(
    r"\b(select|insert|update|delete|drop|alter)\b[\s\S]*(\bfrom\b|\binto\b|\btable\b)", re.I
)


def _walk(value: Any, key: str | None = None) -> list[tuple[str | None, Any]]:
    values: list[tuple[str | None, Any]] = [(key, value)]
    if isinstance(value, Mapping):
        for key, item in value.items():
            values.extend(_walk(item, str(key)))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk(item))
    return values


def validate_untrusted_input(value: str | None) -> None:
    if not value:
        return
    lowered = value.lower()
    if any(pattern in lowered for pattern in _INJECTION_PATTERNS):
        raise GuardrailViolation("Untrusted input attempted to override AI policy")
    if _SQL_PATTERN.search(value):
        raise GuardrailViolation("Raw SQL is not permitted in AI input")
    if any(pattern in lowered for pattern in _SECRET_PATTERNS):
        raise GuardrailViolation("Secret or credential material is not permitted")


def validate_tool_arguments(arguments: Mapping[str, Any]) -> None:
    for key, value in _walk(arguments):
        if key and key.lower() in {"user_id", "owner_id", "account_owner_id"}:
            raise GuardrailViolation("User ownership is injected by the backend")
        if isinstance(value, str):
            validate_untrusted_input(value)


def redact_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    sensitive = {"prompt", "context", "arguments", "authorization", "access_token", "refresh_token"}
    for key, value in metadata.items():
        redacted[key] = "[REDACTED]" if key.lower() in sensitive else value
    return redacted
