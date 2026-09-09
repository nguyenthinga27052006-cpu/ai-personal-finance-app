# Incident Response Runbook

## Severity

SEV1: data loss/exposure, authentication bypass, corrupted balances, or major outage. SEV2: material degradation, worker failure, notification flood or runaway AI cost. SEV3: limited defect without material financial/security impact.

## Lifecycle

Detect -> declare -> contain -> preserve evidence -> investigate -> mitigate -> recover -> communicate -> postmortem.

Finance-specific incidents require stopping unsafe writes, preserving request IDs and audit evidence, validating balances/idempotency and involving the financial-domain owner. For cross-user exposure or compromised secrets, revoke access and rotate through the approved secret process. For database loss, restore only to an isolated target and validate financial invariants before traffic.

Escalation owners: API/platform, DBA, security, AI/product and incident commander. Contact channels are deployment-specific and NOT VERIFIED here.
