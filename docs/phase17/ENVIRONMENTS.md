# Phase 17 Environments

| Environment | Data | Secrets | Artifact | Status |
|---|---|---|---|---|
| local | disposable Compose volumes | `.env`, ignored | local build | LOCALLY VERIFIED |
| staging | dedicated database/cache | dedicated secret-manager namespace | immutable digest | NOT VERIFIED |
| production | dedicated database/cache | dedicated production vault namespace | approved immutable digest | NOT VERIFIED |

Never share database credentials, JWT secrets, worker tokens or AI credentials between staging and production. Templates live in `infra/environments/`; real values are injected by the deployment system.
