# AU-NSW bounded extractor-metrics approval packet

## Scope

This packet requests restricted-local evaluation of the AU-NSW extractor
against the v3 adjudicated holdout evidence. It does not promote the profile,
promote gold labels, publish, redistribute, train, or merge.

## Pinned inputs

| Item | SHA-256 |
| --- | --- |
| v3 annotation report | `c783713789b33cdd3eb25e4cd5b374f0c609fb63c6b4728bf0cf933eed54dd82` |
| v3 reliability report | `dfa2737ce95a18afd76dd2d286ec3881532a306ad7cdda55b245bf42ea3a4d91` |
| Membership | `2acdb55b8679a060175eaca7c2183e90e59a557fb53fc992df45c965275f8d91` |
| Revised codebook | `56c33dd1d681841b5512aa75dc859fa6febb1da687d2b74d9193b40230ebe1c6` |

## Proposed bounded outputs

Compute extractor label/span outputs and descriptive comparison metrics for the
15-unit holdout only, preserving the automated adjudication as candidate
reference evidence rather than promoting it to project gold. Report coverage,
label agreement with the adjudicated candidate reference, exact-span/IoU
metrics, abstention handling, and per-unit disagreement queues. No threshold or
maturity decision is made by the computation.

## Required approval

> I authorize restricted-local AU-NSW extractor evaluation for the exact v3
> 15-unit holdout and pinned inputs in this packet. This authorizes creation and
> validation of descriptive extractor metrics and disagreement queues only. It
> does not authorize gold promotion, profile promotion, maturity decisions,
> publication, redistribution, training, legal certification, push, pull
> request, or merge.
