# ADR-007: Money Representation

- **Status:** Accepted

## Context
Binary floating point can create incorrect financial totals.

## Decision
Store MVP monetary values as signed integers in the smallest currency unit. VND is the default and account currency must match transaction currency.

## Alternatives
Binary floating point, untyped JSON amounts, early multi-currency conversion.

## Consequences
Deterministic arithmetic and simple validation; currency-specific minor-unit policy must be explicit before adding currencies or FX.