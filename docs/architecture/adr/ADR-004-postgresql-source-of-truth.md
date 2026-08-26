# ADR-004: PostgreSQL Financial Source of Truth

- **Status:** Accepted

## Context
Financial records require ACID transactions, relational constraints, ownership queries and deterministic aggregation.

## Decision
Use PostgreSQL as the source of truth for users, accounts, ledger entries and financial domain records.

## Alternatives
Document database, Redis as primary storage, client-side storage.

## Consequences
Reliable relational integrity and reporting; migrations, indexes, backups and restore drills are mandatory.