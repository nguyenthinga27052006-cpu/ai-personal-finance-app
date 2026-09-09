# Phase 17 Rate Limiting

Current API AI protection uses per-user/IP in-memory limits and the Phase 17 usage budget. The limit response is predictable HTTP 429 with a safe error code; events must be counted without secrets.

Production requirements:

- shared store or gateway enforcement across replicas;
- separate authenticated, anonymous and global limits;
- per-feature AI limits;
- emergency global disable/fallback;
- dashboards and alerting for rejected requests.

Distributed enforcement is **NOT VERIFIED**. Do not claim in-memory limits are sufficient for multi-replica production.
