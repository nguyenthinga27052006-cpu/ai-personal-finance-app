# Insight Rules

Phase 10 insights are deterministic derived output. Numeric values come from the
Phase 09 `Financial Facts` analytics overview; insight generation never writes
transactions, accounts, budgets, goals, or balances.

## Thresholds

| Rule | Threshold | Evidence source |
|---|---:|---|
| `spending_change` | absolute growth >= 20% | `comparison.previous.expense_growth` |
| `category_dominance` | top category share >= 50%, with at least two categories | `category_analysis.share` |
| `budget_risk` | utilization >= 80% | `summary.budget_utilization` |
| `cashflow_deficit` | saving < 0, with income > 0 | `summary.saving` |
| `saving_rate_change` | absolute rate change >= 10 percentage points | current and previous `summary.saving_rate` |
| `positive_saving_rate` | saving rate >= 20% and income is non-zero | `summary.saving_rate` |
| `weekend_spending_share` | weekend share >= 40% | `time_analysis.weekend` |
| anomaly | Phase 09 anomaly rule threshold | `anomalies` |

Ranking is deterministic by priority/severity, relevance, confidence, rule ID,
and subject ID.

## Evidence And Lifecycle

Every candidate includes `source`, `rule_id`, `source_metric`, period, subject
when applicable, source value/baseline, and evidence. The ID is a stable hash of
`user_id + rule_id + subject_id + period_start + period_end`; repeated generation
therefore does not duplicate candidates. Candidates expire 30 days after the
period end, and expired candidates are omitted from the active list.

## Insufficient Data

The engine fails closed. It does not emit spending or saving growth without a
previous period, dominance without at least two categories, anomaly insights
without Phase 09 anomaly evidence, or positive saving with zero income. No
recurring insight is emitted because Phase 09 has no canonical recurring-expense
source; the forecast remains `NOT AVAILABLE` for that rule.
