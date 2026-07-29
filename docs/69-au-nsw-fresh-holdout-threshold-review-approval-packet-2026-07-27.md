# AU-NSW fresh holdout threshold and maturity-review packet

## Scope

This packet proposes a restricted-local comparison of the fresh descriptive
reliability artifact with the registered AU-NSW review thresholds. It does not
promote the profile or authorize extractor metrics.

## Pinned evidence

| Item | Value |
| --- | --- |
| Fresh reliability artifact | `3a63a044e7b54c73ef76d6dd877b9dd06965d215cb7e130d0d20323341889ca3` |
| Locked annotation report | `83dfd246d5e51fcb6a05decfb5fd72ac66ca77ede2a16fb59146bcab5c660683` |
| Membership | `2acdb55b8679a060175eaca7c2183e90e59a557fb53fc992df45c965275f8d91` |
| Codebook | `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6` |

## Descriptive comparison

| Measure | Observed | Registered reference |
| --- | ---: | ---: |
| Raw label agreement | 1.000 | >= 0.800 |
| Cohen's kappa | 1.000 | >= 0.600 |
| Exact-span agreement | 1.000 | span review reference 0.500 |
| Abstention agreement | 1.000 | descriptive only |

The 15-unit holdout is small and automated. These results are evidence for
review, not proof of population-wide performance or legal correctness.

## Recommended disposition

Retain `foi-o-au-nsw` as candidate status pending a named maturity decision;
close the specific fresh-holdout span-remediation trigger only if the reviewer
accepts the limited evidence. Extractor evaluation remains a separate gate.

## Required approval

> I authorize restricted-local threshold and maturity-decision review for AU-NSW
> fresh reliability artifact SHA-256 `3a63a044e7b54c73ef76d6dd877b9dd06965d215cb7e130d0d20323341889ca3`,
> using the pinned report, membership, frame, revised codebook, and protocol.
> This authorizes comparison with registered thresholds and preparation of a
> candidate maturity-decision packet only. It does not authorize profile
> promotion, gold promotion, extractor metrics, publication, redistribution,
> training, legal certification, push, pull request, or merge.
