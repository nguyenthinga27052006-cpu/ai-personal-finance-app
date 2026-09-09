# Phase 15 Security Review Report

## Executive Verdict

**PASS WITH RISKS**

No unresolved critical issue or cross-user authorization bypass was found in the reviewed scope. Security hardening added production default fail-closed validation, baseline response headers, request-size rejection, and AI per-user/IP burst limiting with regression tests.

Phase 15 is not production-ready. Several controls require deployment infrastructure or product decisions and remain documented risks.

## Baseline

- HEAD: `ff3ba5b25143edbc046622c28dd48af674a5a3a1`
- Worktree: dirty with extensive pre-existing changes.
- Backend baseline before remediation: 99 passed, 10 deprecation warnings.
- Backend post-remediation: 105 passed, 9 deprecation warnings.
- Flutter baseline: analyzer PASS, 10 tests PASS, APK PASS.
- Runtime verification: `/health` and `/ready` returned HTTP 200; current API image `sha256:32eb9b2296ba412b7cf9867d42cc3b105665eb50c67ab718391ca6c1b5c79e0e` contains the Phase 15 guard and error mapping.
- No migration/schema reset or dependency upgrade was performed.

## Threat Model

See [THREAT_MODEL.md](THREAT_MODEL.md). Assets include credentials, sessions, financial records, receipt candidates, AI context, outputs, logs, and derived recommendations. Main trust boundaries are Flutter/API, API/database, API/worker, API/Gateway/provider, and untrusted user/receipt text into AI guardrails.

## Attack Surface

- Auth endpoints: register, login, refresh, logout.
- Authenticated financial APIs and internal worker endpoints.
- Authenticated AI execute/query endpoints.
- Mobile token storage and API client retry.
- No receipt upload endpoint or object-storage path exists.

## Authentication

**PASS WITH RISKS**

Password hashing uses `pwdlib` Argon2 defaults. JWT issuer/audience/type/expiry are validated, sessions are checked for ownership, expiry, and revocation, and refresh rotation revokes the prior session. Auth endpoints have in-memory per-IP rate limiting and generic invalid-credential responses. Production configuration now rejects default JWT and worker tokens.

Residual: distributed rate limiting, password recovery, device binding, and production secret injection are not implemented/verified.

## Authorization / BOLA

**PASS**

Reviewed account, transaction, category, budget/goal, insight, notification, recommendation, and AI tool paths use authenticated server-derived ownership. Existing tests cover cross-user reads/actions and AI `user_id` injection. No BOLA finding was observed.

## Mass Assignment

**PASS WITH RISKS**

Pydantic request models reject unknown fields in the AI contracts and ownership is server-derived. Existing domain schemas constrain writable fields. A complete endpoint-by-endpoint fuzz matrix was not run.

## Input Validation

**PASS WITH RISKS**

Structured schemas enforce lengths, enums, numeric bounds, date ranges, and pagination bounds in reviewed APIs. A 1 MiB request content-length guard was added at the API middleware boundary. Deep JSON/resource exhaustion limits beyond content length are not comprehensively implemented.

## Rate Limiting

**PASS WITH RISKS**

Auth has in-memory per-IP limiting. AI now has in-memory per-user/IP limiting with a 30 requests/minute default and regression coverage. In-memory limits do not coordinate across replicas and are not a substitute for gateway/WAF controls.

## File Upload

**NOT IMPLEMENTED**

No uploaded-file or object-storage endpoint exists. Receipt extraction is an in-memory/provider abstraction and does not claim upload security. MIME, image, path, signed URL, retention, and deletion controls are deferred until an upload boundary is introduced.

## AI Security

**PASS WITH RISKS**

Prompt/raw SQL/secret/ownership injection guardrails, explicit tool allowlists, structured output validation, canonical service tools, provenance, and disabled write tools are present and tested. Indirect prompt-injection coverage across all stored user text is limited. Real provider behavior is not verified because only the fake provider is enabled.

## AI Data Flow / Minimization

See [AI_DATA_FLOW.md](AI_DATA_FLOW.md). Context is bounded and provenance-bearing; credentials and raw DB access are excluded. External provider retention/compliance is not asserted.

## Logging / Redaction

**PASS WITH RISKS**

AI metadata logs redact prompt/context/arguments/auth tokens and retain safe request/provider/tool metadata. No raw receipt or full financial payload logging was found in reviewed AI code. A production log sink/retention configuration was not available for verification.

## Secret Management

**PASS WITH RISKS**

No committed API/private key pattern was found. Development values exist in local `.env`/templates and compose defaults by design. Production settings now fail closed on development JWT/worker token defaults. Secret rotation/vault integration is not implemented.

## CORS / Headers / TLS

**PASS WITH RISKS**

No permissive CORS middleware was found. Baseline `nosniff`, `DENY`, `no-referrer`, and `no-store` headers are now added. TLS termination, HSTS, production CORS allowlists, trusted proxy configuration, and HTTPS enforcement are deployment responsibilities and were not verified locally.

## Session / Token Security

**PASS WITH RISKS**

Mobile uses `flutter_secure_storage`; logout clears tokens; refresh rotation and revocation are tested. Local API defaults use HTTP for development only. Backup/screenshot/deep-link policies were not independently verified.

## Mobile Security

**PASS WITH RISKS**

No provider secret is present in Flutter code; tokens use secure storage and API ownership is server-side. Android build/analyzer/tests pass. Production TLS/certificate policy and MASVS-level device testing are not verified.

## Backend Security

**PASS WITH RISKS**

No raw SQL/direct AI DB access, unauthorized financial write, cross-user leak, or obvious command/SSRF path was found. Internal worker endpoints use a shared token but are not network-segmented by application code; production network policy is required.

## Dependency Security

**NOT VERIFIED**

The agreed command `pip-audit` is unavailable in the environment (`CommandNotFoundException`). No dependency was upgraded and no package cache was changed. Container and Dart dependency scanning were not available.

## Privacy / Data Inventory

See [DATA_INVENTORY.md](DATA_INVENTORY.md). Inventory exists for identity, sessions, financial data, receipt candidates, AI prompts/context/responses, notifications, recommendations, and logs. No legal basis is asserted.

## Retention / Export / Deletion

**PARTIAL / DEFERRED**

Session revocation exists and posted financial records are not silently hard-deleted. Account-wide export, account deletion cascade policy, receipt deletion, chat deletion, AI log retention, notification deletion, and recommendation deletion workflows are not implemented. These require explicit product/data-lifecycle decisions.

## Error Disclosure

**PASS**

Auth and worker errors use bounded messages; AI errors now map each supported `AIError` subclass to a deterministic public-safe code/message. Regression coverage injects secret-like, SQL-like, authorization, and filesystem content and verifies it is absent from the HTTP response. A broad production error-response matrix was not exhaustively exercised.

## Financial Regression

**PASS**

The final backend suite passed with 105 tests and 9 deprecation warnings. No financial source, schema, migration, transfer/refund, balance, or analytics logic was changed by Phase 15 remediation.

## Security Regression Tests

- Production default secret rejection: PASS.
- Security headers: PASS.
- `Content-Length > 1_000_000` returns bounded HTTP 413 before handler: PASS.
- AI error disclosure regression: PASS; internal exception detail is not returned.
- AI endpoint rate limit: PASS; authenticated endpoint returns HTTP 429 with `rate_limited` under a configured one-request test limit.
- AI rate-limit isolation and injectable-clock window reset: PASS.
- AI prompt injection/raw SQL/secret/ownership guardrails: existing tests PASS.
- Cross-user ownership and financial invariants: existing full suite PASS.
- Upload/path traversal tests: NOT APPLICABLE; upload endpoint is not implemented.

## Remediation Matrix

| ID | Severity | Finding | Fix | Regression Test | Status |
|---|---|---|---|---|---|
| SEC-001 | HIGH | Production accepted development JWT/worker defaults | Fail closed in `Settings` outside development/test | `test_non_development_settings_reject_default_security_tokens` | RESOLVED |
| SEC-002 | MEDIUM | No baseline API security headers/body-size guard | Added middleware headers and 1 MiB `Content-Length` request guard | `test_security_headers_are_present`, `test_oversized_content_length_returns_413_before_handler` | RESOLVED |
| SEC-003 | MEDIUM | AI had no endpoint abuse limit | Added per-user/IP in-memory AI limiter | Endpoint 429 test plus injectable-clock burst/isolation/reset test | RESOLVED WITH SCALING LIMITATION |
| SEC-004 | MEDIUM | Receipt upload/storage boundary absent | Documented as NOT IMPLEMENTED; no insecure path added | N/A | DEFERRED / NOT IMPLEMENTED |
| SEC-005 | MEDIUM | Retention/export/deletion policy incomplete | Created data inventory and explicit lifecycle gap documentation | Documentation review | DEFERRED / PARTIAL |
| SEC-006 | LOW | Dependency scanner unavailable | Recorded NOT VERIFIED; no blind upgrade | N/A | OPEN / NOT VERIFIED |
| SEC-007 | MEDIUM | AI error responses could expose internal exception messages | Added public-safe deterministic error mapping | HTTP response excludes injected secret/SQL/path detail | RESOLVED |

## Remaining Risks

- Shared/in-memory rate limits do not provide distributed abuse protection.
- Production TLS, CORS, HSTS, secret vault/rotation, log retention, and network segmentation require deployment controls.
- Upload/object storage, export/deletion, and durable chat lifecycle are not implemented.
- External provider data handling is not verified.
- Dependency/container/Dart vulnerability scans remain unavailable.

## Final Evidence Reconciliation

- Backend: `105 passed`, 9 deprecation warnings.
- Focused Phase 15 security/configuration tests: `20 passed`.
- Ruff and Python compileall: PASS.
- Flutter analyze: PASS; Flutter tests: `10 passed`; Android debug APK and web builds: PASS.
- Runtime: `/health` 200, `/ready` 200; current image includes the Phase 15 code.
- Security smoke: public-safe AI mapping, live `Content-Length: 1000001` -> HTTP 413, focused AI 429/isolation/reset, unauthenticated AI -> HTTP 401, and required headers: PASS.
- Dependency audit: `NOT VERIFIED`; `pip-audit` unavailable.

## Deferred Items

- Receipt upload and private object storage hardening.
- Privacy retention/export/deletion workflows.
- Production provider compliance and data-processing review.
- Broader AI evaluation and QA remain Phase 16 scope.

## Phase 16 Readiness

Phase 16 is not started or implemented by this review. Security review status is `PASS WITH RISKS`; unresolved medium/deferred infrastructure and privacy risks remain explicitly documented.
