# Phase 13 Acceptance Report

## Status

**PASS WITH NON-BLOCKING ISSUES**

> **Historical / superseded checkpoint:** At the time of this Phase 13 report,
> Phase 14 user-facing AI features had not yet been implemented. The current
> Phase 14 acceptance and runtime closure supersede that statement.

Phase 13 delivers the AI platform foundation only. It does not implement a chatbot, a real provider integration, AI-generated financial writes, Phase 14 user-facing AI features, Phase 15 privacy hardening, or Phase 16 evaluation benchmarking. This phase is not production-ready.

## Objective

Place controlled AI execution above the existing financial system without allowing provider/model input to bypass authentication, ownership, business rules, canonical financial services, or PostgreSQL source-of-truth semantics.

## Architecture

The implemented path is:

```text
Authenticated API -> AI Gateway -> Context Builder / Tool Registry
                  -> canonical services -> data access -> database
```

The module responsibility split is represented by `apps/api/app/ai` and the documented boundaries in `docs/ai/`:

- `context.py`: authenticated execution context, minimized financial context, provenance
- `providers.py`: provider protocol, fake provider, route decision, deterministic fallback
- `gateway.py`: execution orchestration and structured-output validation
- `tools.py`: explicit tool definitions, schemas, registry, read-only adapters, write abstraction
- `guardrails.py`: untrusted input, ownership, SQL, secret, and injection policies
- `schemas.py`: request, response, structured output, and log metadata contracts
- `routes.py`: authenticated `POST /api/v1/ai/execute`

No database migration was added. **Phase 13 does not require a database migration.**

## Provider and Routing Strategy

`Provider.generate()` accepts a structured `ProviderRequest` and returns provider/model/latency/token/cost metadata. `FakeProvider` is the credential-free adapter used for foundation tests. Configuration is environment-backed and contains no credentials. `ModelRouter` deterministically classifies foundation tasks as simple or complex, selects a primary model, and falls back on timeout, unavailable, or provider-response failures. Fallback preserves feature, context, tools, and user scope.

## Context Strategy

`FinancialContextBuilder` calls `build_overview()` and `active_insights()` rather than querying tables or recomputing facts. It limits periods to 366 days, keeps summary/top-five categories/monthly trend/forecast/top-five insights, emits provenance, and marks empty periods as `INSUFFICIENT_DATA`. It does not load the full database or transaction history by default.

## Tool and Authorization Model

Registered read-only tools:

`get_current_balance`, `get_monthly_income`, `get_monthly_expense`, `get_category_spending`, `get_spending_trend`, `get_budget_status`, `get_goal_progress`, `get_recent_transactions`, `get_insights`.

Schemas do not accept `user_id`. The backend injects the current user into `ExecutionContext`; missing auth fails closed, cross-user rows are filtered by existing services, and ownership arguments are rejected. `WriteTool` exists only as an abstraction and always raises `WriteToolsDisabledError`.

## Structured Output and Guardrails

`AIOutput` forbids unknown fields and validates status, answer, citation provenance, and bounded action lists. Malformed JSON and invalid output fail closed. Guardrails reject raw SQL/direct-table instructions, policy/identity/permission prompt injection, secrets, credential payloads, unsupported tools, unauthorized tools, and model/client ownership overrides. Read-only tools have no financial write path.

## Logging and Provenance

AI logs contain request ID, feature, provider/model, latency, optional token/cost metadata, success/error category, selected tool names, fallback state, and routing metadata. Prompts, financial context, auth headers, tokens, secrets, and sensitive arguments are redacted or omitted. Tool/context facts trace to canonical service, period/as-of, calculation type, and deterministic provenance.

## Tests and Validation

Focused Phase 13 contract suite:

```text
python -m pytest apps/api/tests/test_ai_platform.py -q
12 passed, 1 inherited Starlette/httpx deprecation warning
```

The suite covers authenticated access, cross-user isolation, user ID injection, missing auth, no-write behavior, canonical service usage, raw SQL/direct-tool blocking, structured success/failure, malformed provider output, provider timeout, fallback preservation, prompt injection, secret redaction, context minimization, provenance, deterministic behavior, insufficient data, and authenticated HTTP gateway access.

Full regression validation:

```text
python -m pytest apps/api/tests -q: 90 passed, 10 inherited deprecation warnings
python -m ruff check apps/api/app apps/api/tests apps/api/migrations apps/worker/app: PASS
python -m compileall -q apps/api/app apps/worker/app: PASS
python -m alembic -c apps/api/alembic.ini current: c93e2b7f4a18 (head)
python -m alembic -c apps/api/alembic.ini heads: c93e2b7f4a18 (head)
OpenAPI route registration check: PASS
git diff --check: PASS
Docker runtime: PostgreSQL, Redis, API, and worker running; `/health` and `/ready` PASS; authenticated AI gateway smoke returned `INSUFFICIENT_DATA` with provenance and no financial action.
```

## Known Limitations and Deferred Items

- No real external provider adapter or credential/secret integration is enabled; the fake provider is intentional.
- No persistent AI request/evaluation tables or database migration were needed.
- No worker/queue execution for AI requests was added.
- The existing worker runs its first notification/recommendation cycle immediately at startup; when API startup is still in progress that first cycle can log a connection-refused warning, then later cycles remain retry-safe. Worker-to-API connectivity is healthy after startup.
- No full prompt-quality benchmark or golden evaluation dataset was added.
- Full privacy/data-retention hardening remains Phase 15.
- User-facing AI assistant behavior remains Phase 14.
- Write tools remain disabled.
- Existing inherited datetime and Starlette/httpx deprecation warnings remain non-blocking technical debt.
