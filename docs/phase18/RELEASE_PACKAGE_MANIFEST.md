# Release Package Manifest

| Artifact | Identity/status |
|---|---|
| Source | Git SHA `49fe3386bb20900cc7343332fd81a49e52380588` at baseline audit |
| Release version | Mobile `1.0.0+1`; API/worker `0.1.0` |
| API image | `finance-assistant-api:<git-sha>` convention; digest NOT VERIFIED |
| Worker image | `finance-assistant-worker:<git-sha>` convention; digest NOT VERIFIED |
| Mobile APK | Release artifact NOT VERIFIED; prior debug APK evidence exists |
| Web artifact | Prior local web evidence exists; Phase 18 artifact NOT VERIFIED |
| Migration | `c93e2b7f4a18` |
| Environments | `infra/environments/*.env.example` |
| Release notes | `RELEASE_NOTES_V1.md` |
| Smoke report | `RELEASE_SMOKE_TEST_REPORT.md` |
| Architecture | `FINAL_ARCHITECTURE.md` |
| Runbooks | `RUNBOOK_INDEX.md` and Phase 17 runbooks |
| Limitations | `KNOWN_LIMITATIONS.md` |
| Security | `SECURITY_RELEASE_REPORT.md` |
| Backup/restore | `BACKUP_RESTORE_RELEASE_REPORT.md` |

No artifact is presented as store-signed, staging-promoted or production-promoted.
