# AU-NSW fresh holdout candidate maturity decision

## Review scope

This superseded review compared the approved 15-unit fresh-holdout
reliability artifact with the registered descriptive thresholds. It is a
candidate decision packet only; it does not promote `foi-o-au-nsw`.

## Evidence and comparison

| Measure | Observed | Reference | Result |
| --- | ---: | ---: | --- |
| Raw label agreement | 1.000 | >= 0.800 | Meets |
| Cohen's kappa | 1.000 | >= 0.600 | Meets |
| Exact-span agreement | 1.000 | >= 0.500 review reference | Meets |
| Abstention agreement | 1.000 | Descriptive only | Recorded |

Pinned reliability artifact: `3a63a044e7b54c73ef76d6dd877b9dd06965d215cb7e130d0d20323341889ca3`.
The evidence is limited to 15 automated holdout units. The agreement result
supports closing the specific fresh-holdout span-remediation trigger, but is
not sufficient by itself to establish population-wide performance or legal
correctness.

## Candidate disposition

Retain `foi-o-au-nsw` at candidate status. The fresh holdout meets the
registered descriptive references, but profile promotion remains a separate
named approval gate. Extractor metrics were not computed.

## Decision boundary

This packet is invalidated by the annotation-run defect documented in
`docs/71-au-nsw-fresh-holdout-annotation-remediation-2026-07-27.md`. It
authorizes no profile or gold promotion, extractor metrics,
publication, redistribution, training, legal certification, push, pull
request, or merge.
