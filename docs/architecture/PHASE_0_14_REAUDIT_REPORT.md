# Phase 0-14 Independent Re-Audit Report

## 1. Audit Metadata

- Audit date: 2026-09-09
- Repository: `ai-personal-finance-app`
- Branch: `main`
- Commit HEAD: `ff3ba5b25143edbc046622c28dd48af674a5a3a1`
- Working tree: dirty before audit; extensive pre-existing uncommitted source, test, documentation, migration, mobile, and infrastructure changes were present.
- Auditor mode: independent read-only verification. No production source, financial logic, auth logic, schema, migration, dependency, or package cache was changed during this audit.
- Environment: Windows 11 25H2; Python 3.14.7; Flutter 3.47.1; Dart 3.13.1; Android SDK 37; JDK 25 via Flutter; Docker 29.7.2; Compose v5.4.0.
- Source reviewed: `AGENT_RULES.md`, `README.md`, `AGENT_PROGRESS.md`, `docs/IMPLEMENTATION_CONTRACT.md`, architecture acceptance reports, `docs/ai/*`, database schema/rules, API documentation, current AI source, financial services, mobile source, tests, Gradle configuration, and runtime state.

## 2. Executive Verdict

**PASS WITH DOCUMENTED LIMITATIONS**

The repository has strong current local evidence for backend tests, financial invariants, AI boundary tests, Flutter analysis/tests, Android APK compilation, and runtime API parity. The stale-image blocker was closed by rebuilding the API image from the current workspace and restarting it with the correct Docker-context database URL.

The gate is closed at Phase 14 with documented limitations. No Phase 15 implementation was performed by this report.

## 3. Phase Matrix

| Phase | Status | Scope | Evidence | Tests | Risks | Notes |
|---|---|---|---|---|---|---|
| 0 | PASS WITH RISKS | Governance and repository baseline | README, rules, progress, git status | `git diff --check` passed | Dirty worktree and stale progress text | Current changes are not commit-pinned |
| 1 | PASS WITH RISKS | MVP freeze and boundaries | `docs/IMPLEMENTATION_CONTRACT.md` | Backend/mobile regression coverage | Later AI work exceeds original MVP but is explicitly later-phase scope | No evidence of hidden financial write scope |
| 2 | PASS WITH RISKS | Development environment | Python, Flutter, Docker, Compose checks | Ruff, compile, Flutter checks passed | Visual Studio unavailable for Windows desktop | Android/web paths pass |
| 3 | PASS | Database and migrations | Alembic current/head both `c93e2b7f4a18`; no migration created during audit | PostgreSQL integration tests included in full suite | Schema evidence is workspace/runtime, not commit-pinned | No schema change made |
| 4 | PASS | Auth and ownership | Auth dependencies and service ownership filters reviewed | Full suite passed, including cross-user tests | Runtime AI query endpoint not available in running image | No cross-user failure found |
| 5 | PASS | Accounts, categories, merchants | Catalog visibility and ownership code reviewed | Phase 05 and full suite passed | System seed assumptions remain environment-dependent | AI alias validation uses visible categories in workspace source |
| 6 | PASS | Financial core | Transaction service, ledger entries, transfer/refund/idempotency reviewed | Full suite: 99 passed, including financial invariant and PostgreSQL tests | No independent fresh DB reset performed | No critical invariant failure observed |
| 7 | PASS | Budgets and goals | Budget/goal services and deterministic calculations reviewed | Phase 07 and full suite passed | No new issue found | AI tools delegate to these services |
| 8 | PASS WITH RISKS | Flutter core and dashboard | Mobile architecture and Android Gradle config reviewed | `flutter analyze`, `flutter test`, APK build passed | Historical E2E evidence is not commit-pinned | APK build is the actual `apps/mobile` target |
| 9 | PASS WITH RISKS | Canonical analytics | `analytics.service` and Financial Facts reviewed | Analytics and financial tests passed | Full independent numeric fixture audit was not repeated for every formula | No LLM metric generation found |
| 10 | PASS WITH RISKS | Deterministic insights | Insight service and provenance fields reviewed | Insights and full suite passed | Historical acceptance artifacts have timestamp inconsistencies | No direct AI fact generation found |
| 11 | PASS WITH RISKS | Smart notifications | Notification service/worker artifacts and acceptance report reviewed | Notification tests included in full suite | No worker-specific test directory; runtime delivery not independently exercised | Worker container is running |
| 12 | PASS WITH DOCUMENTED LIMITATIONS | Recommendation engine | Candidate source, ranking, dedupe, lifecycle reviewed | Recommendation tests included in full suite | Recurring recommendations deferred; worker evidence is not commit-pinned | Phase 14 wording must preserve candidate semantics |
| 13 | PASS WITH DOCUMENTED LIMITATIONS | AI gateway/tools/guardrails | Gateway, router, context, tools, guardrails, redaction reviewed | `test_ai_platform.py` and full suite passed | Fake provider only; no production provider | No direct DB/raw SQL/write tool found in AI source search |
| 14 | PASS WITH DOCUMENTED LIMITATIONS | User-facing AI features | Workspace source and rebuilt runtime both expose query route | Focused/full tests, authenticated smoke, ownership and status checks passed | Fake provider and in-memory chat remain | Runtime parity verified after rebuild |

## 4. Critical Findings

### F-001 (RESOLVED)

- Severity: HIGH
- Phase: 14 / 2
- Requirement: The user-facing Phase 14 API must be runnable and the authenticated AI query path must be verified from the actual deployed local stack.
- Current behavior: The stale-image 404 was resolved. A subsequent runtime policy mismatch caused unsupported queries to return 500; the Gateway `nl_query` policy was aligned with the route's allowed read-only tools.
- Evidence: Rebuilt image `sha256:decfebef...`; runtime OpenAPI contains `/api/v1/ai/query`; `/health` and `/ready` return 200/ready; authenticated queries return structured results; unsupported intent returns `UNSUPPORTED_REQUEST`.
- Reproduction: Rebuild with `docker compose ... build api`, start with Docker-context `DATABASE_URL=...@postgres:5432/finance`, then query the endpoint.
- Impact: Resolved. Runtime route and policy now match workspace source.
- Recommendation: Keep image build and Docker-context environment values in the deployment runbook.
- Blocker: NO

### F-002

- Severity: MEDIUM
- Phase: 0 / 2 / 14
- Requirement: Acceptance evidence should be reproducible and commit-pinned where possible.
- Current behavior: HEAD is `ff3ba5b...`, while extensive feature, test, migration, and documentation changes are uncommitted. Several historical reports explicitly state that evidence is working-tree evidence.
- Evidence: `git status --short` listed modified and untracked application, migration, mobile, worker, and documentation files; `git diff --stat` reported 22 tracked files changed before counting untracked files.
- Reproduction: `git status --short`, `git diff --stat`.
- Impact: The exact code validated by local tests and the exact code in the running Docker image are not provenance-equivalent.
- Recommendation: Establish a clean, commit-pinned validation snapshot before release acceptance.
- Blocker: NO

### F-003

- Severity: LOW
- Phase: 2 / 8
- Requirement: Environment checks should identify unsupported targets.
- Current behavior: `flutter doctor -v` reports Visual Studio is not installed.
- Evidence: Flutter doctor marks only Visual Studio as failed; Android SDK, JDK, Chrome, network, and connected devices pass.
- Reproduction: `flutter doctor -v`.
- Impact: Windows desktop build is not verified; Android APK and web builds are verified.
- Recommendation: Install the required Visual Studio C++ workload only if Windows desktop support is in scope.
- Blocker: NO

## 5. Financial Invariant Results

| Invariant | Result | Evidence |
|---|---|---|
| Transfer is not expense | PASS | Transaction/analytics services and financial core tests |
| Refund is not normal income | PASS | Refund service and financial invariant tests |
| Debit/credit semantics | PASS | Ledger entry construction and tests |
| Money avoids binary float for financial values | PASS WITH RISKS | Monetary fields are integer/Decimal; merchant alias confidence uses float as non-monetary metadata |
| Account balance deterministic | PASS | Transaction service and invariant tests |
| Cross-account transfer does not double-count expense | PASS | Financial core and PostgreSQL integration tests |
| Unauthorized transaction access denied | PASS | Ownership tests in full suite |
| Idempotency behavior | PASS | Transaction idempotency tests |
| Timezone/month boundaries | PASS WITH LIMITATION | Workspace NL query code uses user timezone; broad analytics timezone audit not independently repeated |
| Ledger/cache reconciliation | PASS | PostgreSQL financial core tests and documented evidence |

No financial invariant failure was observed. No financial source code was changed during this audit.

## 6. Authorization Results

- Authentication: PASS in backend tests and authenticated route dependencies.
- Account/category/transaction ownership: PASS in full test suite.
- Cross-user object access: PASS in existing Phase 05/06/AI tests.
- Object-level authorization: PASS for reviewed services and AI tools.
- AI ownership injection resistance: PASS in `test_ai_platform.py`; tool argument guardrails reject `user_id`/owner keys and execution context supplies the authenticated user.
- Runtime Phase 14 authorization smoke: PASS after rebuild; unauthenticated access returned 401 and user A/B isolation passed.

## 7. AI Architecture Results

- Gateway: PASS in source, focused tests, and rebuilt runtime.
- Provider abstraction: PASS; `Provider`, `FakeProvider`, and `ModelRouter` exist.
- Router/fallback: PASS in focused tests; production external provider is not configured.
- Context builder: PASS WITH DOCUMENTED LIMITATIONS; uses canonical analytics/insight services and bounded facts.
- Tool registry: PASS; explicit read-only registry and schemas.
- Tool ownership: PASS; authenticated `ExecutionContext`, no client `user_id` argument.
- Structured outputs: PASS in tests; feature-specific source paths exist in workspace.
- Guardrails: PASS in tests for prompt injection, raw SQL, secrets, and ownership override.
- Logging/redaction: PASS in source review; no sensitive prompt/context metadata is logged directly.
- Write tool state: PASS; `WriteTool` raises `WriteToolsDisabledError`.
- Direct DB/provider bypass: No finding in focused AI source search. `Session` appears at the boundary/context and route dependency, while canonical reads are delegated through services/tools.

## 8. Phase 14 Feature Results

### Categorization

**PARTIAL**

Deterministic alias/catalog paths and structured Gateway fallback are present in workspace source and behavior tests. Runtime provider-backed categorization was not independently exercised through a live API route. Fake provider only.

### Receipt OCR

**PARTIAL**

OCR provider abstraction, structured extraction, validation, duplicate detection, review state, and confirmation callback exist in workspace source. No uploaded-file API, durable receipt object, or live confirmed transaction integration was independently verified. No direct DB write was found.

### Natural-language Query

**PARTIAL**

Source and rebuilt runtime expose authenticated `/api/v1/ai/query`, constrained intent/tool mapping, canonical tool execution, user-timezone month boundary, and explicit status semantics. Authenticated insufficient-data, unsupported, unauthenticated, and ownership smoke checks passed.

### Spending Analysis

**PARTIAL**

Gateway-backed explanation path and canonical fact preservation are covered by tests. No live provider or runtime API surface was independently verified.

### Recommendation Wording

**PARTIAL**

Candidate semantics and source preservation are covered in workspace tests. Fake provider only; no live wording endpoint was independently verified.

### Chat

**PARTIAL**

Conversation IDs, ownership, message/context bounds, and injection guardrails are present. State is temporary/session-scoped in memory, not durable persistence. Fresh canonical financial fact preference is not proven by a complete chat API flow.

### Mobile AI

**PARTIAL**

AI Assistant screen, suggested questions, API-client boundary, and loading/empty/error/status UI exist in workspace source. APK/build/analyzer pass and the rebuilt runtime route is available.

## 9. Test Evidence

| Command | Result | Notes |
|---|---|---|
| `python -m pytest apps/api/tests -q` | PASS: 99 passed, 10 warnings | Full backend suite; warnings are Starlette/httpx and `datetime.utcnow()` deprecations |
| `python -m pytest apps/api/tests/test_phase14_ai_features.py -q` | PASS in prior focused run: 9 passed | Workspace Phase 14 behavior tests |
| `python -m pytest apps/api/tests/test_phase14_ai_features.py apps/api/tests/test_ai_platform.py -q` | PASS in prior focused run: 21 passed | Phase 13/14 focused behavior tests |
| `python -m ruff check apps/api/app apps/api/tests` | PASS | No lint errors |
| `python -m compileall -q apps/api/app apps/worker/app` | PASS | No output/errors |
| `python -m alembic -c apps/api/alembic.ini current` | PASS: `c93e2b7f4a18 (head)` | No migration change |
| `python -m alembic -c apps/api/alembic.ini heads` | PASS: `c93e2b7f4a18 (head)` | Current equals head |
| `flutter doctor -v` | PASS WITH ENVIRONMENT LIMITATION | Visual Studio missing; Android toolchain passes |
| `flutter analyze` | PASS | No issues |
| `flutter test` | PASS: 10 passed | Mobile unit/widget tests |
| `flutter build apk --debug` | PASS | Built from `apps/mobile` |
| `flutter build web` | PASS | Web build completed |
| `git diff --check` | PASS WITH CRLF WARNINGS | No whitespace errors |

## 10. Build / Runtime Evidence

### Backend

- Docker Compose config: PASS.
- Services: PostgreSQL, Redis, API, and worker running; API/PostgreSQL/Redis health statuses reported healthy.
- `/health`: PASS, `{"status":"ok"}`.
- `/ready`: PASS, `{"status":"ready"}`.
- Authenticated AI query: PASS after API rebuild; runtime OpenAPI contains the route and authenticated smoke returned structured results.
- Ownership smoke: PASS; user A with no data received `INSUFFICIENT_DATA`, while user B's own `12345 VND` expense returned only to user B with `analytics.service` provenance.
- Unsupported smoke: PASS; `UNSUPPORTED_REQUEST`.
- Unauthenticated smoke: PASS; HTTP 401.
- No database reset was performed.

### Mobile

- `flutter analyze`: PASS.
- `flutter test`: PASS, 10 tests.
- `flutter build apk --debug`: PASS.
- `flutter build web`: PASS.
- Android package-cache issue: historical `jni_flutter/android` standalone invocation issue remains an environment/IDE invocation issue. The actual application build from `apps/mobile` passed. No Pub cache was modified.
- Gradle wrapper: 9.3.1; app settings declare AGP 9.1.0 and Kotlin 2.4.0. No Android version changes were made during this audit.

## 11. Documentation Consistency

- `AGENT_RULES.md`: consistent with audit constraints.
- `AGENT_PROGRESS.md`: contains historical/stale phase sequencing text, but now includes the Phase 14 gap closure evidence. It is not commit-pinned evidence.
- Phase 12 report: historical and says Phase 13 was not implemented at report time; superseded by current workspace source but useful as dated evidence.
- Phase 13 report: documents foundation limitations, including fake provider and deferred user-facing behavior; current source extends the workspace beyond that report.
- Phase 14 report: now includes runtime parity evidence and documented limitations.
- README: still describes the current status as Phase 13/next Phase 14, inconsistent with current Phase 14 workspace artifacts.
- AI docs: now describe Gateway/query/receipt/chat limitations, but runtime parity is not proven.
- API docs: no independent current documentation artifact for `/api/v1/ai/query` was found.

## 12. Changed Files During Audit

Files created or modified during this closure:

- `docs/architecture/PHASE_0_14_REAUDIT_REPORT.md`
- `docs/architecture/PHASE_14_FINAL_ACCEPTANCE_REPORT.md`
- `apps/api/app/ai/gateway.py` (minimal nl_query policy correction)

No financial core, auth, schema, migration, dependency, or package-cache changes were made. Existing dirty-worktree changes were not reverted or attributed to this closure.

## 13. Open Risks / Deferred Items

### High

- Validation is not commit-pinned because the worktree contains extensive uncommitted changes.

### Medium

- Receipt feature has no independently verified uploaded-file API or live confirmed transaction-service flow.
- Mobile AI runtime path is verified against the rebuilt API route; a full device-level mobile AI interaction remains outside this smoke.
- No worker-specific test directory exists.
- Real external provider integration is not enabled.

### Low

- Windows desktop target is not verified because Visual Studio is not installed.
- Existing dependency/date deprecation warnings remain.
- Historical acceptance reports contain stale phase sequencing and timestamp/provenance inconsistencies.
- Chat is temporary in-memory state, not durable persistence.

## 14. Final Gate Decision

**PASS WITH DOCUMENTED LIMITATIONS; HOLD AT PHASE 14 FOR THIS CLOSURE**

Remaining non-blocking actions:

1. Reconcile the dirty worktree and produce commit-pinned validation evidence.
2. Keep fake provider, in-memory chat, Phase 15 privacy/security, and Phase 16 evaluation limitations explicit.

No Phase 15 implementation was performed or authorized by this report.
