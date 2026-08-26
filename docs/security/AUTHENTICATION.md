# Authentication

## Scope

Phase 04 provides email/password identity, access tokens, refresh sessions, logout, current-user resolution, and the authentication dependency. Financial resource authorization remains deferred to later phases.

## Password policy

- Minimum 8 characters.
- Maximum 128 characters.
- Empty and whitespace-only passwords are rejected.
- Passwords are not normalized or logged.
- Passwords are hashed with `pwdlib` Argon2id. Plaintext and hashes are never returned by API responses.

## Token strategy

- Access token: JWT HS256, 15-minute lifetime, claims `sub`, `sid`, `type`, `iss`, `aud`, `iat`, and `exp` only.
- Refresh credential: opaque random token, 30-day session lifetime, returned only in the normal auth response and stored on mobile with platform secure storage.
- Database stores only SHA-256 refresh-token hashes.
- Issuer: `ai-personal-finance-api`.
- Audience: `ai-personal-finance-mobile`.
- Clock assumptions: server UTC; database timestamps are interpreted as UTC when a backend returns naive timestamps.

## Identity flow

`Authorization: Bearer <access token>` -> validate signature/issuer/audience/expiry/type -> read `sub` and `sid` -> load user and device session -> require active user and active session.

Request body, query, and client-supplied `user_id` do not determine identity.

## Error contract

Login failures use the generic `invalid_credentials` response and do not reveal whether an email exists. Malformed/invalid/expired access tokens, revoked sessions, inactive users, and invalid refresh sessions return structured `401` errors without internal details.

## Rate-limit hook

`AuthRateLimiter` is the abstraction used by register, login, and refresh. Phase 04 includes a process-local limiter for deterministic protection and tests. A Redis-backed implementation is deferred; no financial policy is embedded in the interface.
