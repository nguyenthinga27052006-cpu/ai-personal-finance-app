# Phase 17 Observability

## Current implementation

The API now emits JSON logs with timestamp, service, level, message, request ID and trace ID. Incoming `X-Request-ID`, `traceparent` or `X-Trace-ID` values are propagated; missing IDs are generated. Responses return `X-Request-ID` and `X-Trace-ID`.

`GET /metrics` exposes local Prometheus-compatible HTTP request counters and p95 duration samples. This is an in-process implementation and is **LOCALLY VERIFIED**, not a distributed production metrics system.

## Correlation

`request_id` is the support/case identifier. `trace_id` is the distributed trace correlation identifier. Logs, metrics labels and future OpenTelemetry spans must use the same values. Financial payloads, tokens and secrets must not be logged.

## Production adapters

Export logs to a managed log platform, metrics to a managed time-series backend, traces through OpenTelemetry, and exceptions to an error tracker with release=`RELEASE` and commit SHA. Provider-specific exporter configuration is **NOT VERIFIED**.
