# Phase 17 Rollback

## Application rollback

Redeploy the previously approved immutable API and worker digests. Do not rebuild from the branch tip.

## Configuration rollback

Restore the previous versioned configuration reference from the secret/config manager. Never print secret values.

## Database rollback

Do not pretend an application rollback reverses a database migration. Prefer backward-compatible expand/contract migrations. For irreversible changes, restore an isolated backup and follow the incident/change-approval procedure.

## Verification

Check `/health`, `/ready`, `/metrics`, financial read paths, worker processing and error rate. Record the old/new digests, migration revision, actor, time and approval.
