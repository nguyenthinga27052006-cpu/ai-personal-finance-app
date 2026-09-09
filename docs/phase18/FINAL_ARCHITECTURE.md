# Final Architecture

```mermaid
flowchart TD
  Flutter[Flutter mobile/web] --> API[FastAPI API]
  API --> Auth[Auth and ownership]
  API --> Domain[Domain services]
  Domain --> PG[(PostgreSQL)]
  API --> Redis[(Redis)]
  API --> AI[AI Gateway]
  AI --> Tools[Read-only tools]
  Tools --> Facts[Financial Facts]
  Facts --> Insights[Insights]
  Facts --> Recommendations[Recommendations]
  Worker[Worker] --> Notifications[Notifications]
  Worker --> Recommendations
  Worker --> Jobs[Scheduled jobs]
  API --> Obs[Local logs/metrics/correlation]
  CI[GitHub Actions] --> API
  CI --> Worker
```

| Component | Status |
|---|---|
| Flutter -> API -> PostgreSQL | IMPLEMENTED / LOCAL ONLY |
| AI gateway/read-only facts/insights/recommendations | IMPLEMENTED / LOCAL ONLY |
| Worker notifications/recommendations/jobs | IMPLEMENTED / LOCAL ONLY |
| Redis | LOCAL ONLY |
| Storage/object storage | EXTERNAL / DEFERRED |
| Prometheus/Grafana/OTel/error provider | EXTERNAL / DEFERRED |
| CI/CD hosted promotion | EXTERNAL / NOT VERIFIED |
