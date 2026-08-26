# ADR-010: AI Tool Boundary

- **Status:** Accepted

## Context
LLMs can misstate financial facts or attempt unauthorized actions if given direct data access.

## Decision
AI communicates only through an AI Gateway and explicitly registered tools. Tools obtain the authenticated user identity server-side, call authorized application services and validate structured outputs. Write tools require authorization, validation, auditability and confirmation when applicable.

## Alternatives
LLM-generated SQL, direct database access, unrestricted autonomous agent.

## Consequences
Grounded and auditable AI behavior; tool schemas, guardrails, evaluation and provider failure fallback are required before enabling AI.