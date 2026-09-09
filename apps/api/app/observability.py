from __future__ import annotations

import json
import logging
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from fastapi import Request

from app.tracing import request_id_context, trace_id_context


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
    duration_counts: Counter[str]
    duration_sums_ms: defaultdict[str, float]
    duration_buckets: dict[str, Counter[float]]

    BUCKETS = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, float("inf"))

    def observe_request(self, route: str, method: str, status: int, duration_ms: float) -> None:
        key = f"{method} {route} {status}"
        self.requests[key] += 1
        duration_key = f"{method} {route}"
        self.duration_counts[duration_key] += 1
        self.duration_sums_ms[duration_key] += duration_ms
        for bucket in self.BUCKETS:
            if duration_ms <= bucket:
                self.duration_buckets.setdefault(duration_key, Counter())[bucket] += 1

    @staticmethod
    def _label(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    def prometheus(self) -> str:
        lines = [
            "# HELP app_http_requests_total HTTP requests by route and status.",
            "# TYPE app_http_requests_total counter",
        ]
        for key, count in sorted(self.requests.items()):
            method, route, status = key.split(" ", 2)
            lines.append(
                "app_http_requests_total{"
                f'method="{self._label(method)}",route="{self._label(route)}",'
                f'status="{status}"}} {count}'
            )
        lines.extend([
            "# HELP app_http_request_duration_ms HTTP request duration in milliseconds.",
            "# TYPE app_http_request_duration_ms histogram",
        ])
        for key, buckets in sorted(self.duration_buckets.items()):
            method, route = key.split(" ", 1)
            for bucket in self.BUCKETS:
                le = "+Inf" if bucket == float("inf") else str(bucket)
                lines.append(
                    "app_http_request_duration_ms_bucket{"
                    f'method="{self._label(method)}",route="{self._label(route)}",le="{le}"}} '
                    f"{buckets.get(bucket, 0)}"
                )
            labels = f'method="{self._label(method)}",route="{self._label(route)}"'
            lines.append(
                f"app_http_request_duration_ms_count{{{labels}}} {self.duration_counts[key]}"
            )
            lines.append(
                f"app_http_request_duration_ms_sum{{{labels}}} {self.duration_sums_ms[key]:.3f}"
            )
        return "\n".join(lines) + "\n"


metrics = Metrics(
    requests=Counter(),
    duration_counts=Counter(),
    duration_sums_ms=defaultdict(float),
    duration_buckets={},
)


def correlation_ids(request: Request) -> tuple[str, str]:
    trace_context = __import__(
        "app.tracing",
        fromlist=["extract_trace_context"],
    ).extract_trace_context(request)
    return trace_context.request_id, trace_context.trace_id
