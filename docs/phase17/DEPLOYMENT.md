# Phase 17 Deployment

## Staging

1. Merge to `main`.
2. CI runs and records commit SHA, tests, migration head and image digests.
3. Deploy the exact API/worker digests to isolated staging.
4. Run migrations using the approved migration job identity.
5. Check `/health`, `/ready`, `/metrics`, API smoke tests and worker heartbeat.
6. Record deployment time, actor and result.

## Production

1. Select a successful staging artifact by digest.
2. Obtain an environment approval.
3. Verify backup freshness and migration compatibility.
4. Deploy API/worker using the same digests.
5. Run expand/contract migrations before code that requires them.
6. Run health/readiness and smoke checks.
7. Monitor error rate, latency, restarts and worker age.

Production deployment is **NOT VERIFIED** because no cloud provider/account was supplied.
