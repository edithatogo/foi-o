# Separate label maturity, epistemic status, review, and extraction method

**Status:** Proposed  
**Date:** 2026-07-09

## Context

FOI-O V2 must add empirical and multi-jurisdiction capability without discarding mature implementation surfaces or overstating public evidence.

## Decision

Use distinct fields and registries for codebook maturity, record epistemic status, review status, and extraction method. Certification is an assertion property requiring human or official authority.

## Consequences

- Consumers can distinguish code maturity from the confidence and review state of an individual assertion.
- Automated extraction remains non-dispositive: model output cannot become certified without human or official authority.
- Producers and validators must populate and test four independent fields instead of relying on a single overloaded status.
- Mappings from legacy status fields require an explicit migration rule and may need human review where the old value was ambiguous.
