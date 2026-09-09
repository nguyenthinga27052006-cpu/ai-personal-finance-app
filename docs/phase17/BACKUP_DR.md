# Phase 17 Backup and Disaster Recovery

## Policy

- PostgreSQL: automated daily full backup plus provider-supported point-in-time recovery where available.
- Retention: 35 daily recovery points and monthly points according to the provider policy.
- Encryption: provider-managed encryption at rest and TLS in transit; backup keys must be separate from application secrets.
- Redis: treat as reconstructible cache; do not use it as financial source of truth.
- Object storage/config: versioning and encrypted retention when introduced.
- Backups must be isolated from the production runtime identity and account.

A backup-success signal is not a restore-success signal. Cloud backup configuration and PITR are **NOT VERIFIED**.

## Ownership

Platform owns schedules, retention and restore drills. Application owners own data-integrity assertions and financial invariant verification.
