# ADR 0003: Distinguish observed, inferred, asserted, and certified claims

## Status

Proposed

## Context

Public request archives contain source labels and correspondence, but many process facts require inference. Agents may generate plausible but non-authoritative claims.

## Decision

Every event and derived field should carry an assertion status: `observed`, `inferred`, `asserted`, `certified`, or `unknown`.

## Consequences

Downstream users can filter on epistemic status and avoid treating model outputs as administrative decisions.
