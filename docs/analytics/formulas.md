# Phase 09 Analytics Formulas

Analytics is a read/derived layer. The canonical facts are Phase 06/07 `transactions` and `transaction_items`; no analytics write changes financial truth.

## Record semantics

Only `POSTED` and non-voided, non-deleted records are loaded. `PENDING` and `VOIDED` are excluded. `INCOME` contributes to income. `EXPENSE` contributes `max(expense.amount - sum(posted child REFUND amounts), 0)` to effective expense. A `REFUND` is never income. `TRANSFER` and `ADJUSTMENT` are excluded from income and expense. A split expense is represented once through its item amounts; the parent amount is not aggregated as another expense. Item allocation follows Phase 07 integer floor allocation, preserving the established rule.

All date periods are inclusive calendar dates in the user's IANA timezone. A day is one local calendar day; a week starts Monday; a month starts on local day 1. Previous period has the same inclusive day count immediately before the current period. Rolling average uses the three preceding equivalent periods. Empty or zero denominators return `0` for ratios and `null` for undefined growth/forecast values. Money is integer minor units. Ratios use exact `Decimal`, rounded half-up to six decimal places. No NaN or Infinity is returned.

## Metrics

| Metric | Formula and contract |
|---|---|
| Total income | Sum of posted `INCOME.amount` in the inclusive local period. Numerator is income minor units; no denominator; empty is 0. |
| Effective expense | Sum of posted `EXPENSE` amounts after all posted child refunds, floored at 0. Refund date does not move the parent expense; it follows Phase 07. Empty is 0. |
| Saving | `total income - effective expense`, in minor units. Negative values are valid. |
| Saving rate | `saving / total income`; zero income returns Decimal 0. |
| Average daily spending | `effective expense / number of local calendar days`, including empty days; zero-length periods are 0. |
| Category share | `category effective expense / total effective expense`; uncategorized is explicit; zero expense is 0. |
| Growth rate | `(current - previous) / previous`; previous zero returns `null`, never an invented percentage. |
| Budget utilization | `effective expense / budget.total_limit`, reusing Phase 07 budget service semantics; zero budget is invalid at the financial boundary. |
| Spending velocity | `effective expense / elapsed local period days`; no elapsed days returns 0. |
| Budget utilization | `effective expense in the requested period / selected owned budget.total_limit`; absent budget returns `null`, mismatched or inaccessible budget is rejected. |

Category and merchant analysis returns amount, record count, share, growth against the previous equivalent period, average, median, and largest amount. Category counts are allocated item counts for split items; merchant counts are expense transaction counts. Missing category and merchant are explicit `Uncategorized` and `Unspecified` groups.

Time analysis emits daily, Monday-based weekly, local monthly, weekday, and weekday/weekend buckets when records exist. Period boundaries use local dates after timezone conversion, including first/last instant boundaries.

## Comparison, anomaly, forecast

Current vs previous uses equal-length immediately preceding periods. Current vs rolling average compares current expense with the arithmetic mean of three preceding equivalent period expenses. Incomplete current periods are not silently extended; the caller's explicit date range is used. Zero baseline yields `null` growth and a zero rolling baseline.

Anomalies are deterministic: `period_spending_vs_rolling_3` is HIGH when current expense is at least 150% of the three-period mean; `large_single_merchant_expense` is MEDIUM when one merchant is one record and at least half of expense and at least 100,000 minor units. Each result includes rule, threshold baseline, value, severity, and reason.

Forecast is a baseline, not a fact. With at least one posted canonical record in the period, it projects the current effective-expense daily pace across the same period length. No recurring-expense source exists in the current schema, so recurring expenses are always 0 and never invented. Empty/insufficient history returns `INSUFFICIENT_DATA` with a null projection.

## Performance and issue classification

The initial implementation performs one indexed user/currency/status transaction query and relationship loads for a request. No cache, materialized view, or read model is introduced. The representative query baseline is recorded by the Phase 09 test/profile command; optimization is deferred until measured latency or query-count evidence requires it.

No Phase 06/07 discrepancy was changed. Phase 09 issues are classified as follows: `AN-001` REQUIRED NOW, severity HIGH, analytics service/API/tests/docs, exact locations are the Phase 09 files, no known issue blocks completion; `AN-002` DEFERRED, severity LOW, recurring-expense source absent from the Phase 06/07 schema, forecast returns explicit insufficient/zero-recurring state, does not block the deterministic baseline.
