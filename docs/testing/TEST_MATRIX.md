# Phase 16 Test Matrix

| Requirement | Test/evidence | Layer | Status | Gate |
|---|---|---|---|---|
| Full backend regression | `python -m pytest apps/api/tests -q` | Integration/unit | 110 passed, 9 warnings | Blocking PASS |
| Transfer neutrality and reconciliation | `test_financial_core.py`, `test_phase06_acceptance.py`, PostgreSQL financial core | Integration | PASS | Blocking |
| Full/partial/over refund and over-refund rejection | `test_financial_core.py`, `test_phase07.py`, `test_phase16_quality.py` | API/integration | PASS | Blocking |
| Split sum and integer boundary validation | `test_financial_core.py`, `test_phase16_quality.py` | API/unit | PASS | Blocking |
| Idempotency and conflict rejection | `test_financial_core.py`, PostgreSQL financial core | API/integration | PASS | Blocking |
| Rollback without partial mutation | `test_phase06_acceptance.py`, PostgreSQL financial core | Integration | PASS | Blocking |
| Ownership/BOLA and AI server-derived ownership | `test_phase06_acceptance.py`, `test_ai_platform.py`, `test_phase14_ai_features.py` | Security/integration | PASS | Blocking |
| Negative API contracts | `test_phase16_quality.py` | API contract | PASS | Blocking |
| Phase 15 security regression | `test_ai_platform.py`, `test_configuration.py`, runtime smoke evidence | Security/API | PASS | Blocking |
| Deterministic AI routing/guardrails/output validation | `test_phase16_quality.py`, `ai_golden_v1.json` | AI contract | PASS: 7/7 cases | Blocking |
| Real-model semantic evaluation | No real provider configured | AI evaluation | NOT VERIFIED | Non-blocking capability gap |
| Representative performance baseline | `test_phase16_quality.py -q -s` | Performance | PASS, baseline only | Non-blocking |
| Flutter analyzer/tests/builds | Flutter commands from `apps/mobile` | Mobile | PASS | Blocking |
| Journey A Flutter E2E | `critical_journey_test.dart` / `critical Phase 08 user journey` | E2E | BLOCKED: Android run stalled without result | Blocking; gate blocked |
| Journey B Budget -> Expense -> Alert | `phase16_journeys_test.dart` / Journey B | E2E | IMPLEMENTED, Android run produced no result | Blocking; gate blocked |
| Journey C Goal -> Contribution -> Progress | `phase16_journeys_test.dart` / Journey C | E2E | IMPLEMENTED, Android run produced no result | Blocking; gate blocked |
| Journey D AI Query -> Tool -> Answer | `phase16_journeys_test.dart` / Journey D | E2E | IMPLEMENTED, Android run produced no result | Blocking; gate blocked |
| Coverage | `python -m coverage --version` | Quality evidence | NOT AVAILABLE | Non-blocking tooling gap |
| CI local gate | `scripts/phase16-gate.ps1` | CI gate | PASS; uses `.venv` and emitted 110 passed, 10 warnings | Blocking |

The authoritative unresolved-item register is [PHASE16_UNPASSED_ITEMS.md](PHASE16_UNPASSED_ITEMS.md). Items marked `NOT VERIFIED`, `NOT AVAILABLE`, or `UNAVAILABLE` are not promoted to `PASS`.
