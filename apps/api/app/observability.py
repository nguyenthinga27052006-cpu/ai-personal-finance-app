from __future__ import annotations

import json
import logging
import time
import uuid
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from fastapi import Request

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "service": "finance-assistant-api",
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
            "trace_id": trace_id_context.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


@dataclass
class Metrics:
    requests: Counter[str]
    durations_ms: dict[str, list[float]]

    def observe_request(self, route: str, method: str, status: int, duration_ms: float) -> None:
        key = f"{method} {route} {status}"
        self.requests[key] += 1
        self.durations_ms.setdefault(f"{method} {route}", []).append(duration_ms)

    def prometheus(self) -> str:
        lines = [
            "# HELP app_http_requests_total HTTP requests by route and status.",
            "# TYPE app_http_requests_total counter",
        ]
        for key, count in sorted(self.requests.items()):
            method, route, status = key.split(" ", 2)
            lines.append(
                "app_http_requests_total{"
                f'method="{method}",route="{route}",status="{status}"}} {count}'
            )
        lines.extend([
            "# HELP app_http_request_duration_ms HTTP request duration in milliseconds.",
            "# TYPE app_http_request_duration_ms summary",
        ])
        for key, values in sorted(self.durations_ms.items()):
            method, route = key.split(" ", 1)
            if not values:
                continue
            ordered = sorted(values)
            p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
            lines.append(
                "app_http_request_duration_ms{"
                f'method="{method}",route="{route}",quantile="0.95"}} {p95:.3f}'
            )
        return "\n".join(lines) + "\n"


metrics = Metrics(requests=Counter(), durations_ms={})


def correlation_ids(request: Request) -> tuple[str, str]:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    trace_id = (
        request.headers.get("traceparent")
        or request.headers.get("x-trace-id")
        or str(uuid.uuid4())
    )
    return request_id, trace_id
