# ADR-001: Modular Monolith

- **Status:** Accepted

## Context
The product has many related domains, but MVP team size and operational needs do not justify distributed services.

## Decision
Use one backend modular monolith with explicit API, application, domain and infrastructure boundaries per module.

## Alternatives
Microservices, a single unstructured application module.

## Consequences
Simpler local development and transactions; modules must preserve boundaries so later extraction remains possible.