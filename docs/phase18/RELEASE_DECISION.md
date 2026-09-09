# Release Decision

## Decision

**CONDITIONAL GO** for a local release candidate only. This is not production approval.

## Conditions / blockers

| ID | Severity | Description | Evidence | Owner | Status |
|---|---|---|---|---|---|
| RC-001 | High | Backup artifact and isolated restore not verified | BACKUP_RESTORE_RELEASE_REPORT.md | DBA/SRE | OPEN |
| RC-002 | High | Release signing/store metadata not ready | APP_STORE_READINESS.md | Mobile/Release | OPEN |
| RC-003 | High | Staging and production deployment not verified | DEPLOYMENT_RUNBOOK.md | Platform | OPEN |
| RC-004 | Medium | Hosted CI/security scan/SBOM results absent | SECURITY_RELEASE_REPORT.md | Platform/Security | OPEN |
| RC-005 | Medium | External monitoring/tracing/error tracking not verified | MONITORING_RELEASE_CHECK.md | SRE | OPEN |

Critical local finance/auth flows have prior PASS evidence, so this is not a local functional NO-GO. The open external and store gates prevent GO.
