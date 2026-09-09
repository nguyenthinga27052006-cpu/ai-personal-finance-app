# Phase 15 Threat Model

## Scope

Security review of the current local architecture. This is a threat model, not a certification or legal privacy assessment.

## Assets

- Credentials, password hashes, access tokens, refresh sessions
- Accounts, balances, transactions, categories, budgets, goals
- Receipt candidates and extracted receipt data
- AI prompts, minimized financial context, outputs, provenance, provider metadata
- Notifications, recommendations, logs, and exported data if later implemented

## Trust Boundaries

- Flutter client -> authenticated API
- API -> PostgreSQL
- API -> Redis
- API -> worker internal endpoints
- API -> AI Gateway -> provider abstraction
- Untrusted user/merchant/receipt text -> AI guardrails
- AI output -> read-only tools or reviewed receipt callback

No object-storage upload boundary exists in the current repository.

## Threat Actors and Controls

| Actor | Threat | Current control | Residual risk |
|---|---|---|---|
| Anonymous attacker | Credential abuse, protected endpoint access | Bearer auth, auth rate limit, generic auth errors | Distributed abuse needs shared limiter/WAF |
| Authenticated malicious user | BOLA, ID tampering, mass assignment | Server-derived user context and ownership queries | Coverage is strongest in backend tests; no external pen test |
| Compromised client | Forged `user_id`, role, state, tool arguments | Pydantic extra-field rejection and AI guardrails | Every new endpoint must preserve the pattern |
| Malicious prompt/receipt text | Prompt injection, raw SQL/tool abuse | Input guardrails, explicit tool registry, structured output validation | Indirect injection corpus is limited |
| Compromised provider | Invented facts or unsafe output | Canonical tools, provenance, output schemas, write tools disabled | Provider compliance/retention is not verified |
| Insider/operator | Log or secret exposure | Metadata redaction and no raw payload logging in AI gateway | Production log platform policy is not verified |

## Security Decisions

- Database remains source of truth.
- AI receives bounded context and cannot choose ownership.
- AI write tools remain disabled.
- Receipt upload/storage is not implemented; no insecure upload path is claimed.
- Production settings reject development JWT and worker-token defaults.
- API adds bounded request-body checks and baseline security headers.

## Open Risks

- Distributed rate limiting, WAF, TLS termination, CORS allowlist, and production secret management must be supplied by deployment infrastructure.
- Durable retention, deletion, and export workflows are not implemented.
- Real provider data retention/compliance is not verified.

## Final Evidence Status

Phase 15 security regression evidence passed: public-safe AI error mapping, the 1 MiB `Content-Length` guard, authenticated AI rate-limit behavior with isolation/window-reset coverage, unauthenticated protected AI access, and baseline security headers. The dependency audit remains `NOT VERIFIED` because `pip-audit` is unavailable.
