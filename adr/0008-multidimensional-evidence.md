# Use multidimensional evidence assertions

**Status:** Proposed  
**Date:** 2026-07-09

## Context

FOI-O V2 must add empirical and multi-jurisdiction capability without discarding mature implementation surfaces or overstating public evidence.

## Decision

Record authority, directness, integrity, temporal applicability, and visibility independently. Retain any A–E grade only as an optional display summary.

## Consequences

- Evidence can be compared without collapsing legal authority, directness, integrity, time, and access into one ordinal grade.
- Consumers that display a summary grade must retain the underlying dimensions and document the deterministic projection.
- Missing or unknown dimensions remain visible instead of being silently treated as weak evidence.
- Validation and comparison tooling must evaluate each dimension independently.
