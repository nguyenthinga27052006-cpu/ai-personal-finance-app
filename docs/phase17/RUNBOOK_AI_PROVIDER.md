# Runbook: AI Provider or Cost Spike

Check provider error/timeout rate, feature usage, budget rejections, fallback count and request IDs. Apply the configured rate limit or disable non-essential AI features. Do not retry unboundedly. Preserve canonical financial reads and never allow AI failure to write financial records. Restore traffic only after latency, error and cost signals return to policy.
