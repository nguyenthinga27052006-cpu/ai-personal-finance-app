# Rollback Runbook

## Decision tree

`DEPLOY -> HEALTH -> SMOKE -> ACCEPT`

Any failure: `DEPLOY -> HEALTH/SMOKE FAILURE -> FREEZE -> ROLLBACK OR FORWARD-FIX -> VERIFY`.

- Application/container: redeploy the previous approved immutable API/worker digest.
- Configuration: restore the previous versioned secret/config reference; never print values.
- Migration: do not claim automatic rollback. Use a compatible forward-fix or isolated restore under change approval.
- Data corruption: stop writes, preserve evidence, restore an isolated copy, validate financial invariants, then decide recovery.
- Dependency/AI failure: disable non-essential AI features or route to the approved fallback; preserve financial read/write safety.

Rollback acceptance requires health, readiness, smoke, financial read checks, worker state and error-rate evidence. Restore execution and data-integrity evidence are NOT VERIFIED.
