# Phase 13 AI Gateway

## Boundary

The authenticated API route `POST /api/v1/ai/execute` is the platform entry point. It injects the authenticated `User` and SQLAlchemy session into an `ExecutionContext`; neither the client nor a provider can select the user scope.

The execution path is:

```text
provider/model -> AI Gateway -> explicit Tool Registry / Context Builder
               -> canonical financial and analytics services -> database
```

The gateway never queries the database directly. It validates feature policy, builds a bounded financial context, executes only explicitly allowed tools, validates provider JSON with `AIOutput`, and returns controlled errors.

## Provider and routing

`Provider` exposes `generate(ProviderRequest)`. `FakeProvider` is the credential-free foundation adapter used in Phase 13 tests. Provider configuration is environment-backed (`AI_PROVIDER`, `AI_MODEL`, `AI_FALLBACK_MODEL`, `AI_TIMEOUT_SECONDS`, `AI_ENABLED`); no provider credential is stored in source.

`ModelRouter` uses deterministic task complexity routing and retries with the fallback provider for timeout, unavailable, or provider-response failures. Fallback requests retain the same feature, context, selected tools, and authenticated execution context.

## Structured output

Providers must return JSON matching `AIOutput`: `status`, `answer`, `citations`, and `suggested_actions`. Unknown fields, malformed JSON, invalid enums, missing fields, and invalid bounds fail closed with `StructuredOutputError`.

## Logging

Only request ID, feature, provider/model, latency, token metadata when available, cost metadata when available, result status, selected tool names, fallback state, and routing metadata are logged. Prompt, context, arguments, authorization headers, tokens, and credentials are redacted or omitted.

Phase 13 uses a fake provider and does not claim production provider readiness.
