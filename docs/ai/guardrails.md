# Phase 13 AI Guardrails

The guardrail layer fails closed for:

- missing authenticated execution context
- model/client supplied `user_id`, `owner_id`, or account-owner fields
- cross-user resource access
- unregistered or feature-disallowed tools
- write capability on the read-only registry
- raw SQL/direct database instructions
- prompt injection attempts that request policy, identity, permission, or secret changes
- secrets, credentials, bearer tokens, and password material in untrusted input
- periods longer than the bounded context policy
- malformed provider JSON or unknown structured-output fields
- unsupported financial facts and empty canonical evidence

User and transaction text is untrusted. It cannot alter tool permissions, ownership, authorization, or system policy. Financial facts are returned with provenance and are sourced from deterministic canonical services. When no posted facts exist, the context is marked `INSUFFICIENT_DATA`; the fake provider does not invent values.

AI logs have a redaction boundary. Prompts, financial context, tool arguments, authorization headers, tokens, and provider secrets are not logged as raw payloads.
