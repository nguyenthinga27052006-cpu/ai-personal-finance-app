# Phase 17 Observability

## Current implementation

The API emits JSON logs with timestamp, service, level, message, request ID and trace ID. Incoming `X-Request-ID` and valid W3C `traceparent` values are propagated; malformed trace context is ignored and missing IDs are generated. Responses return correlation headers.

`GET /metrics` exposes locally aggregated Prometheus exposition with request counters and bounded latency histograms. This is an in-process implementation and is **LOCALLY VERIFIED**, not a production-scale metrics system.

## Correlation

Request correlation is the support/case identifier (`request_id`). Trace-context propagation carries a validated trace ID and parent span ID across the request boundary. Full OpenTelemetry tracing and exporter integration are separate concerns and are **NOT VERIFIED**. Logs and error events use field-name-based recursive sanitization; financial payloads, tokens and secrets must not be logged.

## Verification status

| Capability | Status |
|---|---|
| Request correlation | LOCALLY VERIFIED |
| Trace context propagation | LOCALLY VERIFIED |
| External tracing backend/exporter | NOT VERIFIED |
| Error tracking runtime | LOCALLY VERIFIED |
| External error tracking provider | NOT VERIFIED |
| Prometheus metrics | LOCALLY VERIFIED |
| Production-scale metrics | NOT VERIFIED |

## Production adapters

Export logs to a managed log platform, metrics to a managed time-series backend, traces through OpenTelemetry, and exceptions to an error tracker with release=`RELEASE` and commit SHA. Provider-specific exporter configuration remains **NOT VERIFIED**.
