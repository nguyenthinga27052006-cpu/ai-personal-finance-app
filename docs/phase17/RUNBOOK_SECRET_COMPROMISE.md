# Runbook: Secret Compromise

Revoke and rotate the affected credential in the secret manager, invalidate sessions/tokens where applicable, inspect access logs, remove the secret from build artifacts, and open a security incident. Do not paste the secret into issues or logs. Rebuild from a clean trusted commit and verify no secret scan findings remain.
