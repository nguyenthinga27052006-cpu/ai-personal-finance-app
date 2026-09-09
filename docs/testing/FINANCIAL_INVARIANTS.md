# Phase 16 Financial Invariants

Financial invariant failures are release-blocking. No failure was observed in the executed backend suites.

| Invariant | Implementation source | Test evidence | Expected behavior | Severity |
|---|---|---|---|---|
| Transfer is neither income nor expense | `app/transactions/service.py`, analytics facts | `test_financial_core.py`, `test_phase06_acceptance.py`, PostgreSQL financial core | Entries reconcile to zero at user-total level; source/destination balances reconcile | Blocking |
| Transfer source/destination are distinct, owned, same currency | `create_transfer` | `test_financial_core.py`, `test_phase06_acceptance.py` | Invalid or cross-user transfer is rejected without mutation | Blocking |
| Full and partial refunds are bounded | `_create_refund` | `test_financial_core.py`, `test_phase07.py`, `test_phase16_quality.py` | Refund reduces effective expense; over-refund and double refund are rejected | Blocking |
| Split total equals transaction amount | `TransactionCreate` validator | `test_financial_core.py`, `test_phase16_quality.py` | Exact integer sum is accepted; mismatch/zero item is rejected | Blocking |
| Idempotent retry has one logical operation | transaction service | `test_financial_core.py`, PostgreSQL financial core | Same key/request returns same record; conflicting payload returns 409 | Blocking |
| Financial writes are atomic | transaction service/database transaction | `test_phase06_acceptance.py`, PostgreSQL rollback test | Injected failure leaves no record, entries, items, group, or balance mutation | Blocking |
| Ownership is server-derived | auth dependencies and transaction service | cross-user tests and AI platform tests | Cross-user read/action/tool access is denied | Blocking |
| Ledger/cache reconciliation | `transaction_entries`, account balance updates | `test_phase06_acceptance.py`, PostgreSQL financial core | Cached balance equals opening balance plus signed ledger entries | Blocking |
| Integer money boundaries | Pydantic integer fields and SQL BIGINT | split/amount validation and database foundation tests | No floating-point calculation; positive amounts and deterministic sums | Blocking |

Deferred policy remains explicit for posted edit/void/reversal audit history and persisted audit events. No Phase 16 test changes those semantics.
