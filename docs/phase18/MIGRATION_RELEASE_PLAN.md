# Migration Release Plan

Current migration head: `c93e2b7f4a18`.

## Required sequence

`PRE-DEPLOY -> BACKUP -> MIGRATE -> VERIFY -> SMOKE -> RELEASE`

1. PRE-DEPLOY: pin Git SHA, inspect migration ordering, confirm compatible application/schema pair.
2. BACKUP: create and validate an isolated backup artifact. NOT VERIFIED.
3. MIGRATE: run Alembic once using the migration identity; record current/head.
4. VERIFY: inspect schema, seed idempotency, health/readiness and financial invariants.
5. SMOKE: run the release smoke checklist and record evidence.
6. RELEASE: promote only the exact verified artifact.

The migration chain is ordered through `c93e2b7f4a18`. Automatic database rollback is not assumed. For an incompatible or irreversible migration, use an isolated restore or a forward-fix with change approval. Restore and financial integrity verification are NOT VERIFIED.
