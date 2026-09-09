# Dashboard API

Phase 08 provides an authenticated, read-only dashboard endpoint:

```text
GET /api/v1/dashboard
```

The endpoint derives the current local calendar month from the authenticated
user timezone. It returns:

- total balance across the user's active accounts in the default currency
- current-period income, effective expense, saving, and saving rate
- owned active account balances
- five most recent owned transactions
- current-period category breakdown from Phase 09 Financial Facts
- owned active budget calculations
- owned active goal calculations

All ownership is enforced server-side from the bearer identity. The endpoint
uses the Phase 09 analytics service and existing budget/goal services; it does
not create a parallel financial truth, mutate financial records, or add a cache
or read model.
