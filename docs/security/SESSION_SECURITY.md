# Session Security

## Session record

`device_sessions` is the server-controlled refresh-session record. It stores `id`, `user_id`, `family_id`, a SHA-256 refresh-token hash, `created_at`, `expires_at`, `revoked_at`, `last_used_at`, and optional device, IP, and user-agent metadata.

The effective states are:

- `ACTIVE`: not revoked and not expired.
- `REVOKED`: `revoked_at` is set.
- `EXPIRED`: `expires_at` is in the past.

## Rotation and replay

Every refresh revokes the old record and creates a new record in the same session family. The old opaque credential is never accepted again. Reuse of a revoked credential revokes all still-active records in that family before returning `invalid_refresh_session`.

## Logout

Logout revokes the exact session identified by the access token `sid`. It does not revoke unrelated sessions. Logout also clears mobile secure storage. Logout-all is deferred.

## Storage and logging

Only the refresh-token hash is persisted. Raw refresh tokens, access tokens, passwords, password hashes, and authorization headers must not be logged. IP and user-agent metadata are limited to the fields needed for session context.

## Data safety

The Phase 04 migration is additive and reversible. No financial rows are changed. Session records cascade from their user according to the existing database ownership policy.
