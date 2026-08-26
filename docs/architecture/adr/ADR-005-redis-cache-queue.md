# ADR-005: Redis for Cache and Queue

- **Status:** Accepted

## Context
The system needs transient cache, rate limiting and background job coordination without weakening financial persistence.

## Decision
Use Redis only for cache, queue, rate limiting, transient state and locks. PostgreSQL remains the financial store.

## Alternatives
No cache/queue, Redis as the primary database, Kafka from MVP.

## Consequences
Lower read and job latency; invalidation, expiry, retries and loss of transient state must be handled explicitly.