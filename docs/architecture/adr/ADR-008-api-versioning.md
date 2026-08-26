# ADR-008: Versioned REST API

- **Status:** Accepted

## Context
Mobile clients need a stable contract while backend capabilities evolve.

## Decision
Use REST endpoints under `/api/v1`, typed request/response schemas, standard errors, pagination and request IDs.

## Alternatives
Unversioned routes, GraphQL for MVP, client-specific ad hoc endpoints.

## Consequences
Predictable clients and controlled evolution; breaking changes require a new version or compatibility plan.