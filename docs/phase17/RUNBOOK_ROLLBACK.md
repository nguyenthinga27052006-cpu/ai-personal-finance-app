# Runbook: Bad Deployment or Migration Failure

Freeze promotion and identify current/previous image digests, migration revision, actor and time. Roll back application/config only when schema compatibility is confirmed. For an irreversible migration, restore an isolated database and follow the approved recovery plan rather than pretending a code rollback undoes schema changes. Verify health, readiness, financial reads, worker state and error rate.
