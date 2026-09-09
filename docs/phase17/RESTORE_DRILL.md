# Phase 17 Restore Drill

## Reproducible procedure

1. Identify a backup ID and record start time.
2. Restore into an isolated database/network; never overwrite production.
3. Apply migrations only after inspecting the restored revision.
4. Start API/worker with isolated secrets and environment.
5. Check `/health`, `/ready` and `/metrics`.
6. Verify users, accounts, transactions, budgets/goals and AI provenance rows.
7. Run transfer neutrality, refund bounds, split equality, ownership and idempotency checks.
8. Run a read-only application smoke test.
9. Record completion time, duration, result and failures.

Current local/cloud restore execution: **NOT VERIFIED**. No claim of DR verification is made.
