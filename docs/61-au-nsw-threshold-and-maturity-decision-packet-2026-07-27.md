# AU-NSW threshold and maturity decision packet

This packet records the evidence available for a separately authorized
threshold and maturity decision. It does not make that decision.

## Pinned evidence

| Item | Value |
| --- | --- |
| Reliability artifact | `7bc2469dadf622b9182af6b33eb3fa8dd6cabe9350040b75f46fce287770774f` |
| Locked annotation report | `74125814a8d3da0d161db777e8884847fa5c2bbe1c4f634e8aab228125ee6455` |
| Immutable frame self-pin | `37af88495c8896e83028b4692a10f18f2dd5a5e4dcad6b6140f40312f64d4000` |
| NSW codebook | `3b8d76366e7dccb52e52a5e2275469ea4b52bc54eacff00b89c0bf26a8d6a49f` |

## Registered evidence and thresholds

The registered reliability thresholds are raw agreement `>= 0.80`, Cohen's
kappa `>= 0.60`, and span overlap IoU `0.50`. The observed descriptive values
are raw agreement `0.76`, kappa `0.5867768595`, exact-span agreement `0.30`,
and abstention agreement `0.88`.

These comparisons are reproduced here for decision review; they are not an
automated pass/fail or maturity decision. The evidence is automated and
restricted-local, not human-reviewed or gold-promoted.

## Decision boundary

A named approver must decide whether to retain AU-NSW as candidate, require
codebook/annotation remediation, or take another explicitly documented action.
No profile promotion follows automatically from this packet.

The separate extractor gate remains closed until an ontology-pinned NSW
extractor output bundle is approved. Proposed metrics, if separately
authorized, are precision `>= 0.85`, recall `>= 0.75`, F1 `>= 0.80`, provenance
completeness `>= 0.95`, and unsafe-inference rate `<= 0.01`.

## Required approval

> I authorize restricted-local threshold and maturity decision review for the
> pinned AU-NSW reliability artifact SHA-256
> `7bc2469dadf622b9182af6b33eb3fa8dd6cabe9350040b75f46fce287770774f`.
> This authorizes comparison with the registered thresholds and preparation of
> a candidate maturity-decision packet only. It does not authorize profile
> promotion, gold promotion, extractor metrics, publication, redistribution,
> training, legal certification, push, pull request, or merge.
