# Phase 17 RPO/RTO

Initial targets, not production SLAs:

| Capability | RPO target | RTO target | Assumption |
|---|---:|---:|---|
| PostgreSQL financial data | 15 minutes with PITR | 60 minutes | Managed database supports PITR and isolated restore |
| Redis cache | 24 hours / reconstructible | 30 minutes | Cache is not financial truth |
| API | application state from database | 30 minutes | Immutable image and config are available |
| Worker | queued work within queue retention | 60 minutes | Idempotent jobs and replay policy exist |
| Full application | database plus artifacts | 120 minutes | Approval, backup and runbooks available |

Targets are design assumptions. No production SLO or RTO has been verified.
