# ADR-002: Flutter Mobile

- **Status:** Accepted

## Context
MVP targets Android and iOS with shared financial UI and a feature-first structure.

## Decision
Use Flutter/Dart for mobile. Organize features through View, ViewModel/Controller, Domain/Use Case, Repository and Service layers.

## Alternatives
Separate native Android/iOS apps, a cross-platform framework without the documented architecture.

## Consequences
One mobile codebase and consistent UI; platform-specific secure storage and lifecycle behavior still require tests.