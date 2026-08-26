# Phase 01-03 Master Audit Matrix

**Audit date:** 2026-08-26  
**Scope:** Phase 01 through Phase 03 only. Phase 04 and all business APIs remain excluded.

| Area | Phase 01 Contract | Phase 02 Implementation | Phase 03 Implementation | Evidence | Status | Fix Required |
|---|---|---|---|---|---|---|
| Product scope | MVP V1 defined; later AI/features constrained | Foundation only | No Phase 04 features | contract, API README | PASS | None |
| MVP scope | Auth, accounts, transactions, dashboard, budget, analytics, notifications are product scope | Deferred | No business APIs | contract, main.py | PASS | Keep deferred |
| Tech stack | FastAPI, Flutter, SQLAlchemy, Alembic, PostgreSQL, Redis | Python manifests and Compose | ORM and migration present | pyproject files, Compose | PASS | None |
| PostgreSQL version | PostgreSQL 18 gate required | Compose image 18 | PostgreSQL 18.6 verified through localhost:5433 | Compose ps/version, integration test | PASS | None |
| Redis role | Cache, queue, locks, transient state only | Compose service | Readiness ping only | ADR-005, health.py | PASS | None |
| FastAPI | Backend boundary and versioned API direction | `/health`, `/ready` | No business routes | main.py, health.py | PASS | Keep business routes deferred |
| Flutter | Feature-first client architecture | README scaffold only | No executable project | apps/mobile/README.md | BLOCKED | Flutter/Dart toolchain and project are deferred |
| SQLAlchemy | Persistence ORM | Dependency configured | Models use BigInteger for money | finance.py | PASS | None |
| Alembic | Versioned migrations | Planned | One active head after reconciliation | `alembic heads/history` | PASS | Keep chain checked |
| Repository structure | Modular monolith boundary | API/worker/mobile/infra exist | DB foundation localized | tree, README | PASS | None |
| Environment | Reproducible documented prerequisites | `.env.example`, scripts | Host/container split verified; Flutter/Dart unavailable | check-env.ps1, environment doc | BLOCKED | Install toolchains outside this audit if mobile execution is required |
| Docker | Local reproducible services | Compose exists | Clean no-cache API/worker build passed | Compose build output | PASS | None |
| Health | Runtime health required | `/health` endpoint | Existing container healthy | Compose ps, health.py | PASS | Recheck after clean rebuild |
| Readiness | Dependency readiness required | `/ready` PostgreSQL/Redis ping | HTTP 200 against Docker stack dependencies | health.py, runtime check | PASS | None |
| DB source of truth | PostgreSQL authoritative | Config points to PostgreSQL | Ledger tables present | ADR-004, models | PASS | None |
| Money representation | Integer minor units, 64-bit policy | Not applicable | ORM and initial migration BIGINT | finance.py, migration, verifier | PASS | Keep exact BIGINT assertions |
| Ownership | Server-side ownership | Not implemented | User FKs and cascades only | models, invariant boundaries | IN_PROGRESS | Domain/API authorization deferred |
| Ledger | Entries are source of truth | Not implemented | Structure only | ADR-006, models | IN_PROGRESS | Reconciliation deferred |
| Transfer | Distinct same-owner accounts, balanced entries | Not implemented | Fields/relationships only | contract, integration test | IN_PROGRESS | Domain orchestration deferred |
| Refund | Eligible original, capped/partial policy | Not implemented | Parent link only | contract, model | IN_PROGRESS | Domain policy deferred |
| Split transaction | Item sum equals parent | Not implemented | Table and test only | model, unit/integration tests | IN_PROGRESS | Enforcement deferred |
| Categories | System and user categories | Not implemented | 15 system seed rows | seed.py, seed docs | PASS | None |
| Merchants | Domain/schema direction | Not implemented | Tables and relationships | model/schema | PASS | Business behavior deferred |
| Budgets | MVP product scope | Not implemented | Tables only | model/schema | IN_PROGRESS | Budget logic deferred |
| Goals | P1 direction | Not implemented | Tables only | model/schema | IN_PROGRESS | Goal logic deferred |
| Seed | Idempotent system defaults | Planned | 10 expense + 5 income, app check plus DB unique index | seed.py, migration | PASS | Verify on PG18 |
| Migration | Versioned and coherent | Planned | Single root/head; old conversion root removed | Alembic output | PASS | Fresh PG18 run required |
| Tests | Layered unit/integration evidence | Health unit test | 19 full tests pass; 12 PostgreSQL tests pass on PG18 without skip | pytest output | PASS | None |
| Documentation | Canonical Markdown and ADRs | Foundation docs | Audit artifacts added; stale claims found and corrected | docs | IN_PROGRESS | Finish status synchronization |
| Status/reporting | Evidence-based phase status | No release claims | Phase 01, 02, and 03 status reconciled to evidence | AGENT_PROGRESS.md | PASS | None |

## Boundary Classification

`IMPLEMENTED` means code and evidence exist. `DEFERRED` means intentionally outside this audit's implementation scope. `OUT OF SCOPE` means excluded by the contract. `BLOCKED` means required evidence could not be established. Schema support alone does not make a domain or application rule implemented.
