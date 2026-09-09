# V1 Release Notes

Release candidate: `1.0.0+1`
Release Candidate Identity: `1.0.0+1`
Release Artifacts: NOT VERIFIED
Date: 2026-09-09
Source: `49fe3386bb20900cc7343332fd81a49e52380588` at baseline audit
Status: RELEASE CANDIDATE - LOCALLY VERIFIED WITH DOCUMENTED PRODUCTION/STORE LIMITATIONS

## Highlights

- Authenticated personal finance flows and ownership boundaries.
- Accounts, transactions, transfers, refunds, budgets, goals and notifications.
- Analytics, insights, recommendations and guarded AI read-only features.
- Local observability, correlation, bounded Prometheus metrics and operational runbooks.

## Limitations and deferred work

Hosted CI, staging/production deployment, release signing, store approval, external tracing/error tracking, monitoring backend, backup/restore, security scan results, SBOM, real AI quality and production OCR/object storage remain NOT VERIFIED or DEFERRED.

## Migration and rollback

Migration head is `c93e2b7f4a18`. Follow `MIGRATION_RELEASE_PLAN.md`; application rollback does not automatically roll back database migrations. Use a forward-fix or approved isolated restore.
