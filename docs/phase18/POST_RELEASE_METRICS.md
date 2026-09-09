# Post-Release Metrics

No production values are claimed. Owners and thresholds must be agreed before deployment.

| Metric | Source/calculation | Target/alert | Owner |
|---|---|---|---|
| Request rate | API counter by route | Capacity baseline | Platform |
| p50/p95/p99 latency | Histogram quantiles | Alert on agreed SLO breach | Platform |
| Error/5xx rate | HTTP status counters | Alert on sustained increase | API |
| Health/readiness failures | `/health`, `/ready` probes | Page on sustained failure | Platform |
| Worker failures/backlog | Worker logs/queue metrics | Alert on age/failure threshold | Worker |
| Transaction write failures | API/domain error events | Immediate investigation | Finance/API |
| Idempotency conflicts | Transaction conflict counter | Trend and anomaly alert | Finance |
| Balance reconciliation failures | Financial invariant checks | Critical alert | Finance/DBA |
| AI requests/user/feature | Budget accounting | Budget anomaly alert | AI |
| AI provider latency/failures | Provider telemetry | Fallback/disable threshold | AI |
| AI fallback rate/cost | Gateway/provider usage | Cost threshold | AI/Finance |
| Active users/retention | Product analytics | Product target | Product |
| Notification/recommendation engagement | Event counters | Product target | Product |

Production collection and observed thresholds: NOT VERIFIED.
