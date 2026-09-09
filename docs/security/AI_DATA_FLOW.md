# AI Data Flow and Minimization

## Runtime Path

```text
Flutter
  -> authenticated API route
  -> ExecutionContext(user from server, request ID, allowed tools)
  -> AI Gateway
  -> FinancialContextBuilder / read-only ToolRegistry
  -> FakeProvider or future configured provider
  -> structured validation and provenance
  -> API response
```

Receipt candidates follow a separate reviewed boundary:

```text
OCR provider abstraction -> structured candidate -> validation -> duplicate check
-> review -> explicit confirmation -> existing Transaction Service callback
```

## Data Crossing the Provider Boundary

- Feature/task name
- Bounded financial aggregates from canonical analytics and insight services
- Provenance with source, period, and calculation type
- Explicitly selected read-only tool names and results
- User question or feature input when needed for classification/explanation

## Data Excluded

- Passwords, access tokens, refresh tokens, JWT secrets, worker tokens
- Raw database connections, SQL, arbitrary user IDs, unrelated users
- Full transaction history by default; context is bounded/minimized
- Direct write commands or write-tool capability

## Controls

- Server-derived `ExecutionContext.user`
- Explicit per-feature tool allowlist
- Pydantic structured output validation with unknown fields rejected
- Prompt/raw SQL/secret/ownership guardrails
- Canonical services remain the source of financial facts
- AI write tools disabled
- Metadata logging redacts prompt/context/arguments/token fields

## Limitations

The current provider is fake/local. No external provider retention, residency, training-use, or compliance guarantee is made. Real provider onboarding requires a separate security and privacy review.

Phase 15 verification confirmed that internal AI exception details are mapped to public-safe code/message responses; broader provider and AI evaluation remains outside this phase.
