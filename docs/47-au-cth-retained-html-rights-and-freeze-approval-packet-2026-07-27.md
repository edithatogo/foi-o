# AU-CTH retained-HTML rights and frame-freeze approval packet

## Proposed operation

Create and validate one restricted-local empirical source frame from exactly
the 517 retained AU-CTH HTML records whose text and UTF-8 spans were validated
in the approved bounded operation. This is a subset-only operation: it makes
no claim about the 1,061 JSON-only AU-CTH records or the full 1,578-record
AU-CTH classification.

## Pinned inputs and limits

| Item | Value |
| --- | --- |
| Parent immutable manifest self-pin | `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c` |
| Parent stored-file SHA-256 | `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393` |
| Classification summary | `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab` |
| Retained-HTML candidate summary | `efd5e6be4e588eb3d1f0eaa15104595da41faaa0c89d5b1d3958afbb9f97b8e6` |
| Candidate JSONL | `a09c4b8fc2cf01ca957c3c0c8d3963ab0e0a37253a6fbcf6731cc889a9ed8c34` |
| Exact membership | 517 AU-CTH retained canonical HTML records |
| Protocol | `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf` |
| Codebook | `foio-au-pilot-assertion-v0.2.0`, `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9` |
| Seed | `20260721` |

The frame would record all 517 source records, their immutable text hashes and
spans, the pre-registered clustering rules, and the explicit subset limitation.
It would mark the material restricted-local: no source text may be published,
redistributed, or used for training. The decision is not a legal conclusion
about the original site or individual records.

## Required decision

> I approve the 517-record retained-HTML AU-CTH candidate, summary SHA-256
> `efd5e6be4e588eb3d1f0eaa15104595da41faaa0c89d5b1d3958afbb9f97b8e6` and
> candidate JSONL SHA-256
> `a09c4b8fc2cf01ca957c3c0c8d3963ab0e0a37253a6fbcf6731cc889a9ed8c34`, as
> rights-eligible for restricted-local empirical-frame creation only, subject
> to immutable manifest self-pin
> `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c`.
> I authorize creation and validation of one exact 517-record AU-CTH subset
> frame, including duplicate clustering and the pre-registered seed `20260721`.
> This does not authorize sampling execution, annotation, adjudication,
> extractor metrics, population-wide inference, publication, redistribution,
> training, legal certification, profile promotion, push, pull request, or
> merge.

## Consequence of approval

The next approval would have to name the exact sampled membership produced from
the frozen 517-record subset before blinded packet generation or annotation.
