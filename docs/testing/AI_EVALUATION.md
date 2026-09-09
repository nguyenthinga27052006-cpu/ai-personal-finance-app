# Phase 16 AI Evaluation

Unresolved AI evaluation items are tracked in [PHASE16_UNPASSED_ITEMS.md](PHASE16_UNPASSED_ITEMS.md), especially `P16-AI-EVAL` and `P16-AI-REAL`.

## Dataset

- Version: `phase16-ai-golden-v1`
- Dataset: `docs/testing/ai_golden_v1.json`
- Test: `apps/api/tests/test_phase16_quality.py::test_ai_golden_dataset_contracts_are_deterministic`
- Provider/model: `FakeProvider` / `foundation-simple`
- Scope: deterministic AI platform contract evaluation only.

## Thresholds

Blocking failures:

- Unauthorized tool selection or ownership leak.
- Ungrounded or invented financial facts.
- Wrong critical intent/tool mapping.
- Unsafe write capability.
- Malformed structured output reaching the client.

Non-blocking differences:

- Wording or stylistic variation when facts and provenance remain correct.
- Real-provider availability and semantic quality are not evaluated locally.

## Results

- Dataset schema and required fields: PASS.
- Expense and balance intent/tool mapping: PASS.
- Unsupported request handling: PASS.
- Prompt-injection refusal: PASS.
- Malformed provider output fails closed: PASS.
- Existing ownership, raw-SQL, secret-redaction, tool-allowlist, provenance, and no-write tests: PASS.
- Deterministic AI evaluator: 7/7 cases PASS, with total/passed/failed/skipped/partial counts and per-case reasons printed by the test.

## Golden Field Audit

| Case/field | Evaluation logic | Status |
|---|---|---|
| Intent | `_detect_intent` is compared with expected intent for expense, balance, unsupported, and insufficient-data cases | PASS |
| Tool | `_detect_intent` and `ToolRegistry.execute` are compared with expected tool | PASS |
| Expected args | Tool-specific currency/period arguments are passed to the real registry and checked | PASS |
| Expected status | Success, insufficient-data, unsupported, guardrail, and malformed-output statuses are asserted | PASS |
| Grounding sources | Real `ToolResult.provenance` sources are compared with dataset expectations | PASS |
| Provenance behavior | Real provenance entries and calculation types are required for grounded cases; empty provenance is required for refusals | PASS |
| Numeric fidelity | Dataset numeric facts are compared with canonical tool output (`5000` expense, `95000` balance) | PASS |
| Forbidden claims | Deterministic tool output is checked for forbidden claims | PASS for contract-level output; not semantic model quality |
| Safety | Prompt injection, ownership injection, unsupported scope, and malformed output execute fail-closed paths | PASS |
| Ownership | Golden ownership-injection case calls `validate_tool_arguments`; existing cross-user tests remain green | PASS |
| Insufficient data | Golden empty-user case requires `InsufficientDataError` and no invented number | PASS |
| Unsupported request | Golden unsupported case requires no intent/tool and `UNSUPPORTED_REQUEST` contract | PASS |
| Malformed output | Malformed provider content must raise `StructuredOutputError` | PASS |

This is a deterministic platform contract audit, not a semantic model-quality evaluation. The evaluated fields are PASS only for the FakeProvider/platform contract; they do not establish real-model quality.

## Not Verified

No real provider/model is configured. Semantic intent accuracy, answer quality, hallucination rate, model groundedness, provider retention/compliance, and production-model numeric fidelity are `NOT VERIFIED`. No accuracy percentage is claimed.
