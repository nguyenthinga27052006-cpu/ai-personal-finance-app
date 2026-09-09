from __future__ import annotations

import re
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from fastapi import Request

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="-")
span_id_context: ContextVar[str] = ContextVar("span_id", default="-")

_TRACEPARENT_RE = re.compile(
    r"^(?P<version>[0-9a-fA-F]{2})-(?P<trace_id>[0-9a-fA-F]{32})-"
    r"(?P<parent_id>[0-9a-fA-F]{16})-(?P<flags>[0-9a-fA-F]{2})$"
)


def _valid_traceparent(value: str) -> tuple[str, str] | None:
    match = _TRACEPARENT_RE.fullmatch(value.strip())
    if not match:
        return None
    version = match.group("version")
    trace_id = match.group("trace_id")
    parent_id = match.group("parent_id")
    flags = match.group("flags")
    if version.lower() == "ff" or trace_id == "0" * 32 or parent_id == "0" * 16:
        return None
    if int(flags, 16) & 0xFE:
        return None
    return trace_id.lower(), parent_id.lower()


@dataclass(frozen=True)
class TraceContext:
    request_id: str
    trace_id: str
    parent_span_id: str = "-"
    span_id: str | None = None

    def __post_init__(self) -> None:
        if self.span_id is None:
            object.__setattr__(self, "span_id", uuid.uuid4().hex[:16])

    def to_headers(self) -> dict[str, str]:
        return {
            "X-Request-ID": self.request_id,
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
        }


def build_trace_context(
    *,
    request_id: str | None = None,
    trace_id: str | None = None,
    parent_span_id: str | None = None,
    span_id: str | None = None,
) -> TraceContext:
    normalized_request_id = request_id or str(uuid.uuid4())
    normalized_trace_id = trace_id or str(uuid.uuid4())
    return TraceContext(
        request_id=normalized_request_id,
        trace_id=normalized_trace_id,
        parent_span_id=parent_span_id or "-",
        span_id=span_id,
    )


def extract_trace_context(request: Request) -> TraceContext:
    traceparent = request.headers.get("traceparent")
    if traceparent:
        parsed = _valid_traceparent(traceparent)
        if parsed:
            trace_id, parent_span_id = parsed
            return build_trace_context(
                request_id=request.headers.get("x-request-id") or str(uuid.uuid4()),
                trace_id=trace_id,
                parent_span_id=parent_span_id,
            )

    return build_trace_context(
        request_id=request.headers.get("x-request-id") or str(uuid.uuid4()),
        trace_id=request.headers.get("x-trace-id") or str(uuid.uuid4()),
        parent_span_id=request.headers.get("x-span-id") or "-",
    )


def set_current_trace(context: TraceContext) -> tuple[Any, Any, Any]:
    request_token = request_id_context.set(context.request_id)
    trace_token = trace_id_context.set(context.trace_id)
    span_token = span_id_context.set(context.span_id or "-")
    return request_token, trace_token, span_token


def reset_current_trace(tokens: tuple[Any, Any, Any]) -> None:
    request_token, trace_token, span_token = tokens
    request_id_context.reset(request_token)
    trace_id_context.reset(trace_token)
    span_id_context.reset(span_token)
