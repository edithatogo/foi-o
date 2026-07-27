# AU-NSW corrected threshold-review approval packet

## Scope

This packet requests restricted-local comparison of the corrected AU-NSW
fresh-holdout reliability artifact with registered descriptive references. It
does not authorize profile promotion, extractor metrics, or publication.

## Pinned evidence

| Item | SHA-256 |
| --- | --- |
| Corrected reliability | `13dd6b83e354481f717f2d4df0f182c53243d6e55e5ebe21e6f184cdea4e54b2` |
| Corrected annotation report | `13512e12edd236e5097548024b9332751c736bbcec9117beeda10ba0af642871` |
| Membership | `2acdb55b8679a060175eaca7c2183e90e59a557fb53fc992df45c965275f8d91` |
| Revised codebook | `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6` |

## Comparison for review

| Measure | Observed | Registered reference |
| --- | ---: | ---: |
| Raw label agreement | 0.867 | >= 0.800 |
| Cohen's kappa | 0.727 | >= 0.600 |
| Exact-span agreement | 0.333 | span review reference 0.500 |
| Abstention agreement | 0.867 | descriptive only |

The label and kappa references are met, while exact-span agreement remains
below the review reference. The sample is only 15 automated holdout units, so
this is not population-wide evidence.

## Required approval

> I authorize restricted-local threshold and maturity-decision review for
> corrected AU-NSW reliability artifact SHA-256
> `13dd6b83e354481f717f2d4df0f182c53243d6e55e5ebe21e6f184cdea4e54b2`, using
> the pinned corrected annotation report, membership, immutable frame, revised
> codebook, and protocol. This authorizes threshold comparison and preparation
> of a candidate maturity-decision packet only. It does not authorize profile
> promotion, gold promotion, extractor metrics, publication, redistribution,
> training, legal certification, push, pull request, or merge.
