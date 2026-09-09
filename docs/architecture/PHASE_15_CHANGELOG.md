# Phase 15 Changelog

## CODE

- Added production configuration validation rejecting development JWT and worker-token defaults outside development/test.
- Added baseline security headers and a 1 MiB content-length request guard.
- Added per-user/IP in-memory AI rate limiting for `/api/v1/ai/*`.
- Added public-safe deterministic AI error mapping for all supported `AIError` subclasses.
- Made AI route request/limiter dependencies required rather than optional.

## TEST

- Added regression tests for production security-default rejection.
- Added security-header coverage.
- Added `Content-Length > 1 MiB` -> HTTP 413 coverage.
- Added AI error disclosure regression coverage.
- Added authenticated AI endpoint HTTP 429 coverage.
- Added limiter burst/isolation/window-reset coverage with an injectable test clock.

## MIGRATION

- Added migration: NO
- Migration ID: NONE

## CONFIG

- Runtime behavior now fails closed for default security tokens outside development/test.
- No dependency/version changes.

## MOBILE

- No mobile source changes.

## INFRA

- No Docker/CI infrastructure source changes. Production TLS/CORS/WAF remain deployment responsibilities.

## DOCS

- Added `docs/security/THREAT_MODEL.md`.
- Added `docs/security/DATA_INVENTORY.md`.
- Added `docs/security/AI_DATA_FLOW.md`.
- Added `docs/security/PHASE_15_SECURITY_REVIEW_REPORT.md`.
- Added `docs/architecture/PHASE_15_FINAL_CHECKPOINT.md`.
- Added `docs/architecture/PHASE_INDEX.md`.
- Updated `AGENT_PROGRESS.md`.

## GENERATED

- No generated artifacts intentionally changed.

Database:

- Added migration: NO
- Schema changed: NO

Dependencies:

- Changed: NO

Package cache:

- Changed: NO

Financial core:

- Changed: NO

## FINAL EVIDENCE RECONCILIATION

- Backend final validation: 105 passed, 9 deprecation warnings.
- Focused Phase 15 security/configuration validation: 20 passed.
- Ruff, compileall, Flutter analyze, 10 Flutter tests, Android debug APK, and web build: PASS.
- Runtime `/health` and `/ready`: HTTP 200. Current API image: `sha256:32eb9b2296ba412b7cf9867d42cc3b105665eb50c67ab718391ca6c1b5c79e0e`.
- Security smoke: public-safe AI error, 1 MiB `Content-Length` -> HTTP 413, AI 429, unauthenticated AI -> HTTP 401, and headers: PASS.
- Dependency status: `NOT VERIFIED`; agreed `pip-audit` command unavailable. No package installation or dependency change was made.
- Final verdict: PASS WITH RISKS.
