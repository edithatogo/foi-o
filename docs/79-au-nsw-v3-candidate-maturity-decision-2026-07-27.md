# AU-NSW v3 candidate maturity decision

## Review scope

This restricted-local packet compares the approved v3 descriptive reliability
artifact with registered references. It is a candidate disposition only and
does not promote `foi-o-au-nsw`.

## Comparison

| Measure | Observed | Reference | Result |
| --- | ---: | ---: | --- |
| Raw label agreement | 0.867 | >= 0.800 | Meets |
| Cohen's kappa | 0.727 | >= 0.600 | Meets |
| Exact-span agreement | 1.000 | >= 0.500 | Meets |
| Abstention agreement | 0.867 | Descriptive only | Recorded |

Pinned reliability artifact: `dfa2737ce95a18afd76dd2d286ec3881532a306ad7cdda55b245bf42ea3a4d91`.
The result is based on 15 automated holdout units. It supports closing the
specific span-remediation trigger, but does not establish population-wide
performance or legal correctness.

## Candidate disposition

Retain `foi-o-au-nsw` at candidate status. The registered descriptive
references are met, but profile promotion requires a separate explicit gate.
Extractor metrics were not computed.

Profile promotion, gold promotion, publication, redistribution, training,
legal certification, push, pull request, and merge remain unauthorized.
