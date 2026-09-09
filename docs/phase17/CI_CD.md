# Phase 17 CI/CD

## Promotion

`pull request -> CI -> main -> immutable artifact -> staging -> approval -> production`.

The workflow in `.github/workflows/ci.yml` runs backend tests with PostgreSQL/Redis services, worker compile checks, Flutter analysis/tests/build, container builds, artifact metadata, secret scanning and dependency auditing.

## Identity and artifacts

- Commit SHA is the CI build identity.
- Container tags use `${GITHUB_SHA}`; staging/production templates require registry digests.
- Production must promote the exact artifact tested in staging; it must not rebuild.
- CI artifacts include JUnit output and image metadata.
- Pull requests never deploy production. Production approval is a deployment-environment policy owned by the platform team.

## Verification

Workflow file: `/.github/workflows/ci.yml`. GitHub-hosted execution is **NOT VERIFIED** locally. Local equivalents are covered by `scripts/phase16-gate.ps1` and the Phase 16 evidence.
