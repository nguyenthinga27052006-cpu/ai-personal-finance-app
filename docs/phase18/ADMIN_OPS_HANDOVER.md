# Admin and Operations Handover

ADMIN UI NOT IMPLEMENTED.

Operational access is through controlled deployment, database, worker, logs and metrics tooling. Access must use least privilege, named identities, MFA, short-lived credentials and audited emergency access. Secrets belong in the environment-specific secret manager, not source control.

- Admin access: no application admin UI; operational owner uses approved platform identity.
- Database access: migration identity for migrations; read-only diagnostic identity for investigation.
- Worker control: deploy/scale/restart through approved deployment identity.
- Logs/metrics: read-only observability access; never expose financial payloads or secrets.
- Secrets: secret-manager access only for service identity and authorized operators.
- Incident access: time-bound emergency access with approval and post-incident review.

Actual cloud access model: NOT VERIFIED.
