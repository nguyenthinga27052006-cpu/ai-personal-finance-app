# Runbook: Backup or Restore Failure

Check last successful backup, age, retention, encryption/key access and provider job logs. A green backup job is insufficient: run an isolated restore drill, migrations, health checks and financial invariant verification. Escalate when the freshness target is breached. Never overwrite production during diagnosis.
