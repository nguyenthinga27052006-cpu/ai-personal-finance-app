# Phase 14 Final Acceptance Report

## Executive Verdict

**PASS WITH DOCUMENTED LIMITATIONS**

The Phase 14 runtime blocker is closed. The API image was rebuilt from the current workspace source, the route appeared in runtime OpenAPI, the container was restarted with the correct Docker-network database URL, and authenticated AI query, ownership, unsupported-intent, insufficient-data, and unauthenticated checks passed.

This is not a production-readiness claim. The local contract intentionally uses a fake provider; chat remains temporary/session-scoped in memory; privacy/security hardening and AI evaluation remain deferred to later phases.

## Blocking Findings

The previous blocker was a stale runtime image returning `404 Not Found` for `POST /api/v1/ai/query`.

Resolution:

- Rebuilt `api` with `docker compose ... build api` from the current workspace.
- Restarted `api` without resetting PostgreSQL or Redis volumes.
- Corrected the runtime invocation to use `DATABASE_URL=postgresql://...@postgres:5432/finance` inside Compose. The earlier `localhost:5433` value was a host-side URL and caused `/ready` to fail inside the container.
- Fixed the minimal Gateway policy mismatch for `nl_query`, which had caused unsupported questions to return HTTP 500 after the route became reachable.

No blocking Phase 14 finding remains in the verified local runtime.

## Runtime Evidence

- Repository HEAD: `ff3ba5b25143edbc046622c28dd48af674a5a3a1`
- Worktree: dirty with extensive pre-existing uncommitted changes; validation is not commit-pinned.
- Runtime image: `sha256:decfebefdef940f561ae1c53a499d07a2cd54fcd75954a94d88ed0705ec1e795`
- Image created: `2026-09-09T06:35:11.201135241Z`
- Container recreated from that image at `2026-09-09T06:35:16.140246241Z`.
- Runtime OpenAPI: `/api/v1/ai/query` present with POST operation and bearer security.
- `/health`: `{"status":"ok"}`.
- `/ready`: `{"status":"ready"}`.
- Compose services: API healthy, PostgreSQL healthy, Redis healthy, worker running.
- No database reset or migration was performed.

## AI Feature Evidence

### Categorization

**IMPLEMENTED WITH LIMITATIONS**

- Deterministic merchant alias/catalog path precedes Gateway fallback.
- Candidate categories are validated against visible system/user categories.
- Gateway fallback uses structured output and supports low-confidence/invalid-category fail-closed behavior.
- No financial write occurs.
- Local provider is `FakeProvider`; no external provider was enabled.

### Receipt OCR

**PARTIAL**

- OCR provider abstraction and fake provider exist.
- Structured extraction validates merchant, date, currency, total, items, and reconciliation.
- Duplicate detection produces review-required state.
- Explicit confirmation is required before delegating to the existing transaction-service callback.
- No direct DB write exists in the receipt feature.
- Uploaded-file/object-storage integration is not implemented and remains deferred to later privacy/security scope.

### Natural-Language Query

**IMPLEMENTED WITH LIMITATIONS**

- Runtime route: `POST /api/v1/ai/query`.
- Runtime OpenAPI route parity: PASS.
- Authenticated no-data query: `INSUFFICIENT_DATA` with no guessed amount.
- Unsupported question: `UNSUPPORTED_REQUEST`.
- Authenticated user B with a canonical `12345 VND` expense received `SUCCESS`, `12345 VND`, tool `get_monthly_expense`, and `analytics.service` provenance.
- User A without that data received `INSUFFICIENT_DATA`.
- Default month period uses the authenticated user's timezone and exact calendar month end.

### Spending Analysis

**IMPLEMENTED WITH LIMITATIONS**

- Canonical facts are prepared before Gateway explanation.
- Provider wording cannot replace canonical values/source in the wrapper.
- Behavior tests cover Gateway execution and numeric preservation.
- Fake provider only; no production external provider.

### Recommendation Wording

**IMPLEMENTED WITH LIMITATIONS**

- Recommendation candidate remains the source of type, reason, confidence, expected impact, and estimate semantics.
- Gateway wording path is covered by behavior tests.
- Invented numeric/source changes are not accepted by the wrapper contract.

### Conversation / Chat

**PARTIAL**

- Conversation IDs are user-owned.
- Cross-user conversation access is denied.
- Message count and context token bounds are enforced.
- State is explicitly **TEMPORARY / SESSION-SCOPED / IN-MEMORY**.
- Durable conversation persistence is not implemented and no migration was added.

### Mobile AI

**IMPLEMENTED WITH LIMITATIONS**

- Widget: AI Assistant screen.
- API boundary: mobile `AIGateway` -> `ApiClient` -> authenticated `/api/v1/ai/query`.
- Suggested questions, loading, ready/empty, result status, and provider/network error states are present.
- No provider call or financial calculation exists in Flutter UI.
- Android app build from `apps/mobile` passed.

## Authorization Evidence

- Unauthenticated `POST /api/v1/ai/query`: HTTP 401.
- User A cannot see User B's financial data.
- User B's canonical expense was returned only in User B's query.
- AI tool arguments do not accept client ownership identifiers.
- Server-side `ExecutionContext.user` supplies ownership.
- Existing Phase 13 and full-suite tests cover `user_id` injection and cross-user isolation.

## Financial Boundary Evidence

- AI uses read-only canonical tools/services for financial facts.
- No raw SQL or direct transaction insert exists in the AI feature path.
- `WriteTool` remains disabled.
- Receipt confirmation delegates to the existing transaction service boundary.
- Transfer/refund/ledger/balance invariants were not modified.
- Full financial/backend test suite passed.

## Mobile Evidence

- `flutter analyze`: PASS.
- `flutter test`: PASS, 10 tests.
- `flutter build apk --debug`: PASS from `apps/mobile`.
- `flutter build web`: PASS.
- Historical `jni_flutter/android` standalone Gradle issue was not used as acceptance target and Pub cache was not modified.
- `flutter doctor -v` reports Visual Studio missing, so Windows desktop is not verified; Android is verified.

## Test Evidence

| Command | Result |
|---|---|
| `python -m pytest apps/api/tests -q` | PASS: 99 passed, 10 warnings |
| `python -m pytest apps/api/tests/test_phase14_ai_features.py apps/api/tests/test_ai_platform.py -q` | PASS: 21 passed, 1 warning |
| `python -m ruff check apps/api/app apps/api/tests` | PASS |
| `python -m compileall -q apps/api/app apps/worker/app` | PASS |
| `flutter analyze` | PASS |
| `flutter test` | PASS: 10 passed |
| `flutter build apk --debug` | PASS |
| `flutter build web` | PASS |
| `git diff --check` | PASS, CRLF normalization warnings only |

## Known Limitations

- Fake provider is the only local provider; production external provider integration is not enabled.
- Chat is temporary/session-scoped in-memory state, not durable persistence.
- Receipt uploaded-file/object-storage and privacy hardening remain deferred to Phase 15 scope.
- AI evaluation/benchmarking remains deferred to Phase 16 scope.
- Worktree is dirty and evidence is not commit-pinned.
- Existing dependency/date deprecation warnings remain non-blocking.

## Changed Files

During this closure:

- `apps/api/app/ai/gateway.py` - corrected `nl_query` allowed-tool policy.
- `docs/architecture/PHASE_0_14_REAUDIT_REPORT.md` - reconciled resolved runtime blocker and evidence.
- `docs/architecture/PHASE_14_FINAL_ACCEPTANCE_REPORT.md` - created this final acceptance report.

The API image was rebuilt locally. No database schema, migration, financial core, package cache, or dependency version was changed.

## Phase 15 Readiness

Phase 14 acceptance is closed with documented limitations. This report does not implement or authorize Phase 15. Phase 15 remains the next planned phase for privacy/security hardening only after normal project approval.

**PHASE 14 = PASS WITH DOCUMENTED LIMITATIONS**

**NEXT = PHASE 15**
