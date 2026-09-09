# Runbook: Container Crash Loop or Disk Exhaustion

Check restart count, exit code, healthcheck output, memory/CPU limits, writable paths, disk usage and image digest. Compare with the last approved artifact. Preserve logs, stop runaway retries, scale only through approved configuration, and verify health/readiness plus metrics after recovery. Escalate storage or node faults to the platform owner.
