# Infrastructure Templates

Phase 17 provides provider-neutral environment templates and Docker Compose development support.

- `environments/local.env.example`: local-only values.
- `environments/staging.env.example`: staging contract; secrets and immutable image digests are injected by trusted CI.
- `environments/production.env.example`: production contract only; it is not a deployable secret file.
- `docker/docker-compose.dev.yml`: local development stack.

Cloud-specific networking, managed database/cache, secret manager, registry, monitoring and backup resources are **NOT VERIFIED** because no cloud provider/account was supplied. Production must use isolated staging/production databases and secrets, immutable image digests, approval gates and documented migration/rollback procedures.
