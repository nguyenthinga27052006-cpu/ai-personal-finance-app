# Runbook: Database Slow or Unavailable

Check readiness, connection usage, query latency, locks, storage and provider events. Protect the database from retries and do not write around the source of truth. For slow operation, capture query evidence and scale only through approved infrastructure. For outage, preserve the incident timeline, restore only into an isolated target and run financial invariant checks before traffic. Never claim restore success without data-integrity evidence.
