# ADR-009: Authentication Strategy

- **Status:** Accepted

## Context
The mobile client needs short-lived access and renewable sessions, while financial APIs require server authentication.

## Decision
Use email/password registration and login with short-lived access tokens plus revocable refresh sessions. Store refresh credentials in platform secure storage; never store raw passwords or tokens in logs.

## Alternatives
Long-lived access tokens, client-only authentication, biometric-only authorization.

## Consequences
Revocation and rotation can protect sessions; password hashing, rate limits, token expiry and server-side authorization are required.