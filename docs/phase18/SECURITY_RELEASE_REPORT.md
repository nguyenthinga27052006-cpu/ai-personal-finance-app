# Security Release Report

| Control | Status | Note |
|---|---|---|
| Secret templates/defaults | LOCALLY VERIFIED | Production values must come from a secret manager |
| JWT production validation | LOCALLY VERIFIED | Existing configuration tests |
| Headers/request size | LOCALLY VERIFIED | Existing Phase 15/16 evidence |
| CORS/TLS assumptions | NOT VERIFIED | Deployment controls absent |
| Ownership/BOLA | LOCALLY VERIFIED | Existing backend tests |
| Rate limits | LOCALLY VERIFIED | In-memory/local only |
| Docker non-root | LOCALLY VERIFIED | Dockerfile review/build evidence |
| CI security workflow | CONFIGURED | Workflow contains gitleaks/pip-audit steps |
| Gitleaks result | NOT VERIFIED | No hosted execution result |
| pip-audit result | NOT VERIFIED | No current scan result |
| Container scan | NOT VERIFIED | No scanner result |
| SBOM | NOT VERIFIED | No SBOM artifact |

Configured scanner != executed scanner. No vulnerability-free claim is made.
