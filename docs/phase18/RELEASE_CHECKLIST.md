# Release Checklist

| Section | Status | Evidence | Owner | Notes |
|---|---|---|---|---|
| SOURCE | LOCALLY VERIFIED | baseline audit | Engineering | SHA pinned |
| BUILD | PARTIAL | reproducible build plan | Release | Fresh RC artifacts pending |
| DATABASE | LOCALLY VERIFIED | migration plan/head | DBA | Restore gate open |
| SECURITY | NOT VERIFIED | security report | Security | Scanner results/SBOM pending |
| AUTH | LOCALLY VERIFIED | Phase 16 evidence | API | External deployment pending |
| FINANCIAL | LOCALLY VERIFIED | Phase 16 evidence | Finance/API | Restore integrity pending |
| AI | LOCALLY VERIFIED | Phase 16/17 evidence | AI | Real provider quality pending |
| MOBILE | PARTIALLY READY | store readiness | Mobile | Release signing pending |
| STORE | NOT READY | store readiness | Release | IDs/assets/legal pending |
| OBSERVABILITY | LOCALLY VERIFIED | monitoring check | SRE | External backend pending |
| BACKUP | NOT VERIFIED | backup report | DBA/SRE | Artifact pending |
| RESTORE | NOT VERIFIED | backup report | DBA/SRE | Drill pending |
| DEPLOYMENT | NOT VERIFIED | deployment runbook | Platform | Staging/production pending |
| ROLLBACK | DOCUMENTED | rollback runbook | Platform | Exercise pending |
| DOCUMENTATION | LOCALLY VERIFIED | Phase 18 package | Engineering | This package |
| HANDOVER | DOCUMENTED | HANDOVER.md | Operations | Access owners pending |
