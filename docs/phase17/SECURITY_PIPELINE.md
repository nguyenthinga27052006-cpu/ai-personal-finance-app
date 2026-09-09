# Phase 17 Security Pipeline

CI includes secret scanning, dependency audit, container build and image metadata. Production policy should add a blocking container scanner, SBOM generation, license policy, signed provenance and digest-only deployment references.

No secrets are stored in this repository. `.env.example` contains placeholders only; real environment files are ignored. Production JWT, database, worker and AI credentials belong in a dedicated secret manager with rotation and emergency-revocation procedures.

Gitleaks, dependency, container, SBOM, signing and license checks are configured or specified, but hosted CI execution is **NOT VERIFIED**.
