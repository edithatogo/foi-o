# AU-NSW candidate maturity-decision packet

## Scope

This is a restricted-local candidate decision packet based only on the pinned
automated reliability result. It records the threshold comparison and a
recommended disposition; it is not a named-human maturity decision and does
not promote the profile.

## Evidence

| Measure | Observed | Registered threshold | Comparison |
| --- | ---: | ---: | --- |
| Raw label agreement | 0.76 | >= 0.80 | Below registered minimum |
| Cohen's kappa | 0.5867768595 | >= 0.60 | Below registered minimum |
| Exact-span agreement | 0.30 | IoU-based span review at 0.50 | Descriptive span divergence requires review |
| Abstention agreement | 0.88 | Reported descriptively | No automatic decision |

Pinned reliability artifact: `7bc2469dadf622b9182af6b33eb3fa8dd6cabe9350040b75f46fce287770774f`.
The observed values are from 100 automated paired annotations, with 10,000
singleton-cluster bootstrap replicates and seed `20260721`.

## Candidate disposition

Recommended disposition: retain `foi-o-au-nsw` as a candidate profile and open a
codebook/span-remediation queue. Do not promote, publish, redistribute, train,
or treat this result as legal certification. This recommendation is not a
final maturity decision; a named approver must accept, reject, or revise it.

The high disagreement volume and low exact-span agreement should be reviewed
before any extractor evaluation. Extractor metrics remain separately gated and
were not computed.

## Required decision

> I record the AU-NSW candidate maturity review for reliability artifact
> SHA-256 `7bc2469dadf622b9182af6b33eb3fa8dd6cabe9350040b75f46fce287770774f`.
> I accept the candidate disposition of retaining `foi-o-au-nsw` at candidate
> status and opening a codebook/span-remediation queue. This does not authorize
> profile promotion, gold promotion, extractor metrics, publication,
> redistribution, training, legal certification, push, pull request, or merge.
