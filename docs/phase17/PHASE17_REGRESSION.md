# PHASE 17 REGRESSION

## Date

2026-09-09

## Git

- Branch: `main`
- Source verification HEAD: `f569550`
- Implementation baseline: `b3c07aa`
- Phase 17 implementation commits: `b017e4f`, `691009d`, `7bd23da`, `8d2dd0d`, `f2105d5`, `b3b555b`
- Documentation reconciliation commit: current final HEAD from `git rev-parse HEAD`.
- Working tree: source/report files remain untracked; generated temporary artifacts are removed and final status is recorded separately.

## Phase 16 Regression

- Command: `scripts\\phase16-gate.ps1`
- Historical Phase 16 baseline: 110 backend tests.
- Authoritative backend command: `python -m pytest apps/api/tests -q` collected 119 items, with 119 passed, 0 failed, and 9 warnings.
- Focused Phase 17 command: `python -m pytest apps/api/tests/test_phase17_operability.py -q` passed 9 tests.
- Ruff: `python -m ruff check apps/api/app apps/api/tests` passed.
- Compileall: `python -m compileall -q apps/api/app` passed.
- Financial regression: PASS; no Phase 17 financial logic regression was identified.
- Full Phase 16 gate: backend 119 passed and 10 warnings; Ruff and compileall passed; Flutter analyze reported 33 pre-existing informational `avoid_print` findings; 11 Flutter tests passed; debug APK and web builds passed.

## Phase 17 Tests

- `apps/api/tests/test_phase17_operability.py`: 9 focused tests.
- Trace tests: valid propagation, malformed/short/non-hex traceparent rejection, and fallback behavior.
- Sanitization tests: field-name redaction, recursive mappings, ordinary-word preservation, and traceback correctness.
- Runtime error test: sanitized capture, request/trace IDs, release/environment, and safe 500 response.
- Metrics tests: bounded histogram storage, route-template labels, and Prometheus parser/format validation.
- AI usage budget test: verifies per-user/per-feature isolation, hard-stop behavior, retry-after value, and daily reset boundary.
- Current backend total: 119 passed, 0 failed, 9 warnings in the authoritative direct command.

## CI/CD

- Local verification: workflow file and five job groups were reviewed; YAML/configuration structure is present for backend, worker, Flutter, containers, and security.
- Hosted verification: NOT VERIFIED; no hosted GitHub Actions run evidence is available.
- Artifact identity and production approval/staging concepts are documented, not externally exercised.

## Containers

- API: local Docker build succeeded; image was reported at approximately 312 MB.
- Worker: local Docker build succeeded.
- Non-root: Dockerfiles define `appuser`/uid `10001`.
- Healthcheck: API healthcheck is configured.
- Scanner: NOT VERIFIED; no container scan result or SBOM was generated.

## Observability

- Logging: local structured JSON formatter implemented and reviewed.
- Request correlation: LOCALLY VERIFIED by focused runtime tests.
- Trace context propagation: LOCALLY VERIFIED by strict traceparent tests.
- External tracing backend/exporter: NOT VERIFIED; no OpenTelemetry exporter configured.
- Error tracking runtime: LOCALLY VERIFIED by focused runtime test.
- External error tracking provider: NOT VERIFIED; no provider execution evidence.
- Prometheus metrics: LOCALLY VERIFIED by histogram and parser tests.
- Production-scale metrics: NOT VERIFIED; no multi-process or hosted backend evidence.
- Alerts: rules/runbooks documented, but no monitoring backend or external alert routing was exercised.

## Backup / Restore

- Backup: procedure exists in `scripts/backup-restore-drill.ps1` and related documentation; backup artifact creation is NOT VERIFIED.
- Restore: NOT VERIFIED; no actual restore execution was evidenced.
- Financial integrity: NOT VERIFIED; no restored database was checked.
- RPO: DOCUMENTED / NOT VERIFIED; target only, not measured.
- RTO: DOCUMENTED / NOT VERIFIED; target/method only, not achieved or measured.

## AI Cost Control

- User scope: locally verified per-user accounting.
- Feature scope: locally verified per-feature accounting.
- Budget: locally verified daily budget and hard-stop enforcement.
- Rate limit: local route/layer retained and reviewed; distributed enforcement NOT VERIFIED.
- Retry: provider retry protection NOT VERIFIED.
- Model routing: real-provider routing and quality evaluation DEFERRED.

## Security

- Secret scan: CI job configured; result NOT VERIFIED.
- Dependency scan: CI job configured; result NOT VERIFIED.
- Container scan: NOT VERIFIED.
- SBOM: NOT VERIFIED; no artifact generated.
- Environment isolation: local/staging/production templates exist; deployed isolation NOT VERIFIED.

## Deployment

- Staging: template and deployment documentation exist; staging deployment NOT VERIFIED.
- Production: template and approval concept exist; production deployment NOT VERIFIED.
- Rollback: procedure documented and locally reviewed; execution NOT VERIFIED.

## Runbooks

Nine runbooks exist: API down, database, queue, AI provider, backup, rollback, secret compromise, container, and cost spike. Document presence was verified; incident exercises are NOT VERIFIED.

## Limitations

- Hosted CI execution is unavailable in this local evidence set.
- No staging or production deployment evidence exists.
- Backup artifact, restore execution, restored financial integrity, and DR drill are unverified.
- RPO/RTO are targets, not measured results.
- Distributed rate limiting/shared AI accounting is not verified.
- OpenTelemetry exporters, external error tracking, monitoring, and alert routing are not verified.
- Security scan outputs and SBOM are not verified.
- Real-model AI evaluation and production model routing remain deferred.
- Direct backend test warnings include one Starlette/httpx deprecation and eight SQLAlchemy `datetime.utcnow()` deprecations. The Phase 16 gate reports one additional warning from its environment.

## Final Verdict

**PASS WITH DOCUMENTED LIMITATIONS**
