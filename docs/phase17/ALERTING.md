# Phase 17 Alerting

| Alert | Initial condition | Severity | Response |
|---|---|---|---|
| API availability | health/readiness failure for 5 minutes | critical | RUNBOOK_API_DOWN |
| API errors | 5xx > 2% for 5 minutes | high | RUNBOOK_API_DOWN |
| API latency | p95 > 750 ms for 10 minutes | high | RUNBOOK_API_DOWN |
| Database | pool saturation or connection failures | critical | RUNBOOK_DATABASE |
| Worker | job age > 15 minutes or failure rate > 5% | high | RUNBOOK_QUEUE |
| AI provider | timeout/error spike or budget breach | high | RUNBOOK_AI_PROVIDER |
| Backup | last successful backup older than 24 hours | critical | RUNBOOK_BACKUP |
| Infrastructure | CPU > 80%, memory > 85%, disk > 80%, repeated restart | high | platform runbook |

Each production alert must have an owner, dashboard link, response action and escalation path. Rules are design targets; firing is **NOT VERIFIED** without a monitoring backend.
