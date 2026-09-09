# Runbook: API Down

Detection: health/readiness alert or elevated 5xx.  
Diagnosis: inspect deployment revision, container status, logs by request/trace ID, database/Redis readiness and recent migration.  
Mitigation: stop promotion, restart only through the deployment controller, or route to last approved digest.  
Recovery: validate `/health`, `/ready`, `/metrics`, authenticated smoke test and error rate.  
Escalation: platform owner, database owner if readiness fails.  
Post-incident: record commit/digest, timeline, root cause and prevention.
