# AU-CTH empirical-frame-freeze approval packet

## Proposed operation

Freeze one restricted-local AU-CTH empirical source frame derived from the
already finalized 2,082-record AU RightToKnow immutable manifest. This packet
is a proposal only: it does not create the frame, sample its units, generate
annotation packets, or execute annotation.

## Exact scope and pins

| Item | Value |
| --- | --- |
| Parent immutable manifest self-pin | `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c` |
| Parent stored-file SHA-256 | `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393` |
| Parent population | 2,082 canonical RightToKnow request pages |
| Retained AU-CTH classified records | 1,578 |
| Excluded AU-NSW records | 179 |
| Excluded out-of-scope records | 115 |
| Excluded unresolved records | 210 |
| Classification-summary SHA-256 | `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab` |
| Protocol | `docs/41-v2-sampling-and-annotation-protocol.md`, SHA-256 `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf` |
| Sampling design | `docs/42-australian-pilot-preregistration.md`, SHA-256 `4264bcad4b2b83ffe6df312626f7b3ea285f9b19a1b40aa0952b4358c08d9118` |
| Approved codebook | `foio-au-pilot-assertion-v0.2.0`, SHA-256 `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9` |
| Seed | `20260721` |

The frame would retain the exact 1,578 `AU-CTH` members from the already
validated four-way classification. It would record every other parent member
as excluded, with its existing classification reason. It would apply the
pre-registered duplicate-clustering rules before any sampling: canonicalized
request title/body/provider/jurisdiction exact clusters, plus same-family near
duplicates at 5-gram MinHash Jaccard >= 0.90 or normalized Levenshtein >= 0.92.
Clusters are atomic and there is no replacement after freezing.

The proposed frame is restricted-local and rights-bounded. It may be used only
to construct the governed frame and subsequent candidate sampling artefacts;
it cannot be published, redistributed, used for training, or treated as a
legal conclusion. The prior immutable-manifest approval established no right
to annotate or disclose source material.

## Required decision

> I approve freezing one restricted-local AU-CTH empirical source frame of
> exactly 1,578 classified records, derived only from immutable manifest
> self-pin `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c`,
> stored-file SHA-256
> `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393`, and
> classification-summary SHA-256
> `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab`.
> Apply the sampling protocol SHA-256
> `9e8415e60c90d8feba2290c5a97aa1a03f7200978fb6b212f5df54ed99b44caf`,
> preregistration SHA-256
> `4264bcad4b2b83ffe6df312626f7b3ea285f9b19a1b40aa0952b4358c08d9118`,
> approved codebook `foio-au-pilot-assertion-v0.2.0` SHA-256
> `ed1f4f1ee9b0442ed8570e0591f0c2a8dc498dbb8bf0f09df49b4eee779ca8b9`,
> seed `20260721`, and the stated exclusion and duplicate-clustering rules.
> This authorizes local frame creation and validation only. It does not
> authorize sampling execution, annotation, adjudication, extractor metrics,
> publication, redistribution, training, legal certification, profile
> promotion, push, pull request, or merge.

## Consequence of approval

An approval permits a single hash-pinned source-frame manifest and a validator
result. A further approval must identify the exact sampled membership and
authorize any blinded annotation execution; it cannot be inferred from this
freeze decision.
