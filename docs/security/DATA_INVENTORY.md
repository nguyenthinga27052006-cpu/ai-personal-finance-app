# Phase 15 Data Inventory

| Data category | Source | Purpose | Storage/access | Provider recipient | Retention/deletion/export | Status |
|---|---|---|---|---|---|---|
| Identity/profile | Auth registration/current user | Authentication and personalization | PostgreSQL; authenticated owner | None by default | Account lifecycle policy not implemented | PARTIAL |
| Password credentials | Registration | Authentication | Password hash in PostgreSQL; never returned | None | Account deletion policy not implemented | PASS WITH LIMITATIONS |
| Access/refresh sessions | Login/refresh | Session authentication and revocation | PostgreSQL session rows; owner/auth service | None | Revocation exists; retention policy not documented | PARTIAL |
| Financial data | Accounts/transactions/budgets/goals | Core finance and canonical analytics | PostgreSQL; server ownership checks | AI provider only through bounded context when enabled | Financial history is not silently deleted | PASS WITH LIMITATIONS |
| Receipt data | Current receipt candidate abstraction | Review before transaction posting | In-memory candidate only; no upload storage | OCR provider abstraction only; fake provider local | No durable receipt retention/deletion exists | NOT IMPLEMENTED |
| AI prompt text | Authenticated AI request | Intent/classification/explanation | Request memory/provider request; metadata redacts prompt/context | Fake provider locally; external provider disabled | Durable AI log retention not implemented | PARTIAL |
| AI financial context | Context Builder | Grounded explanation/tool execution | Bounded aggregates/provenance | Provider abstraction | Provider retention is not verified | PASS WITH LIMITATIONS |
| AI response/provenance | Gateway output | User response and audit metadata | API response and safe metadata logs | Provider returns structured output | Durable response retention not implemented | PARTIAL |
| Notifications | Deterministic rules | In-app alerts | PostgreSQL, user-scoped | None | No deletion/export workflow | PARTIAL |
| Recommendations | Deterministic candidates | User guidance | PostgreSQL, user-scoped | Wording provider only when used | No deletion/export workflow | PARTIAL |
| Logs/metadata | API/AI/worker runtime | Operations/security | Runtime logging platform | No provider secrets by design | Platform retention policy not verified | PARTIAL |

No legal basis or regulatory conclusion is asserted. Production retention, export, deletion, and provider contracts require deployment/product decisions.

Phase 15 evidence does not change these data-lifecycle limitations: retention, export, deletion, receipt upload/object storage, and external-provider compliance remain incomplete or unverified.
