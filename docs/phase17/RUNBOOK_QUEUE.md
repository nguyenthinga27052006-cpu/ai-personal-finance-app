# Runbook: Queue or Worker Failure

Check worker health, queue depth, oldest job age, retry count and worker logs. Pause producers if duplicate or destructive behavior is suspected. Replay only idempotent jobs. Deploy the previous approved worker digest if the failure follows a release. Verify scheduler locks, notification/recommendation outcomes and queue age after recovery.
