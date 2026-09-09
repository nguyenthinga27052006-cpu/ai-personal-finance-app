# AI Documentation

AI gateway, tool schemas, data minimization, evaluation and provider policies belong here.

Phase 14 user-facing AI wrappers use the Phase 13 Gateway and canonical read-only tools.
Natural-language queries are exposed at `POST /api/v1/ai/query`; the mobile AI Assistant
consumes that API. Receipt extraction remains a reviewed candidate flow: OCR/extraction,
validation, duplicate detection, explicit confirmation, then delegation to the existing
transaction service. Chat remains temporary/session-scoped in-memory state with bounded,
user-owned conversation IDs. There is no real external provider or durable conversation
storage in this phase; see [../IMPLEMENTATION_CONTRACT.md](../IMPLEMENTATION_CONTRACT.md).
