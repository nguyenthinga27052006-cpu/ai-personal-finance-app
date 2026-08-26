# ADR-003: FastAPI Backend

- **Status:** Accepted

## Context
The backend needs typed API validation, async support and proximity to Python analytics/OCR/AI libraries.

## Decision
Use Python with FastAPI for the HTTP backend, split into domain modules and APIRouters.

## Alternatives
Django, Node.js, a framework-free Python HTTP service.

## Consequences
Strong OpenAPI/schema support and a suitable Python ecosystem; dependency and async correctness must be managed explicitly.