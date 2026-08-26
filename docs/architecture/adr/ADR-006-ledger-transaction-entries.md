# ADR-006: Ledger Transaction Entries

- **Status:** Accepted

## Context
A transaction row alone cannot model account effects consistently for expenses, income, transfers, refunds and splits.

## Decision
Represent financial account effects in `transaction_entries`. A transfer is one transaction with distinct source/destination entries; cached account balance is derived/checked from the ledger.

## Alternatives
Only a mutable transaction balance column, separate expense and income records for transfers.

## Consequences
Clear accounting semantics and reconciliation; write operations must atomically create all related records.