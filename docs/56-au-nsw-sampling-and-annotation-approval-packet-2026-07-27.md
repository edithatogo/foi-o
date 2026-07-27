# AU-NSW sampling and annotation protocol approval packet

## Proposed bounded protocol

This packet proposes the exact next protocol for the already immutable
restricted-local AU-NSW frame. It does not draw a sample, generate packets,
annotate, adjudicate, compute metrics, or promote the profile.

### Pinned inputs

| Item | Value |
| --- | --- |
| Immutable frame self-pin | `37af88495c8896e83028b4692a10f18f2dd5a5e4dcad6b6140f40312f64d4000` |
| Immutable frame stored SHA-256 | `d09deb2ce966fb1b13ef33244f542a4c897df534baaeab94e7bc064c10643176` |
| Jurisdiction and regime | `AU-NSW` / `GIPA` |
| Eligible frame population | 115 text-bearing units |
| Excluded from frame | 64 metadata-only units, retained in the parent candidate ledger |
| Proposed codebook | `examples/v2/au-nsw-assertion-codebook.v0.2.0.pending.json`, SHA-256 `3b8d76366e7dccb52e52a5e2275469ea4b52bc54eacff00b89c0bf26a8d6a49f` |
| Proposed seed | `20260721` |
| Proposed annotator roles | `agent:au-nsw-annotator-a`, `agent:au-nsw-annotator-b` |
| Proposed adjudicator role | `agent:au-nsw-adjudicator` |

## Codebook and unit rules

Each assertion receives exactly one primary label: `observed`, `inferred`,
`candidate`, or `unknown`; one optional UTF-8 half-open source span; an
abstention flag; and an abstention reason from `missing_evidence`,
`insufficient_evidence`, `out_of_scope`, or `other`. The agents must abstain
rather than infer a label from platform state or legal assumptions.

The primary unit is one request-linked assertion. Every unit retains its
request slug, source URL, Internet Archive timestamp, raw SHA-256, text SHA-256,
and immutable frame self-pin. No attachments, linked pages, or live-origin
content may be added.

The previously approved `foio-au-pilot-assertion-v0.2.0` hash is AU-CTH
specific and cannot be used for this NSW run. The NSW candidate codebook above
therefore requires its own hash-bound approval before packet generation.

## Exclusions

The 64 metadata-only records are excluded before annotation because they have
no retained request text. No replacement units may be drawn. Any of the 115
text-bearing units later found malformed or outside the approved AU-NSW/GIPA
scope must remain in the ledger with one of these reasons:

`wrong_jurisdiction_or_regime`, `non_public_or_access_restricted`,
`rights_ineligible`, `unresolved_identity`, `malformed_or_unreadable`, or
`non_request_material`.

## Sample-size justification and selection

The eligible population is 115, which is smaller than the preregistered
proportion-planning target of 385. The empirical frame therefore uses a census
of all 115 eligible units; no population-estimation sampling weights apply.

For bounded reliability workload, select exactly 100 of the 115 units without
replacement using a version-pinned deterministic PRNG, seed `20260721`, after
sorting by canonical unit digest. The 100-unit paired annotation workload is
not a prevalence estimate and must not be pooled with any enriched sample.
The remaining 15 units stay in the immutable frame and are not silently
replaced. All 115 units have singleton exact-text duplicate clusters, so no
cluster crosses the annotation workload boundary.

## Reliability thresholds

Report raw agreement and Cohen's kappa with two-sided 95% cluster-bootstrap
intervals using 10,000 replicates and seed `20260721`; report kappa as
undefined with a reason if a marginal is constant. The proposed minimum gate
is raw agreement `>= 0.80` and kappa `>= 0.60` for each primary label family.
For spans, report exact-span agreement and overlap F1 at intersection-over-union
`0.50`. Any failure remains a candidate result and opens a disagreement queue;
it does not trigger automatic promotion or threshold relaxation.

Extractor metrics are not authorized by this packet. If later authorized, the
proposed metrics are precision `>= 0.85`, recall `>= 0.75`, F1 `>= 0.80`,
provenance completeness `>= 0.95`, and unsafe-inference rate `<= 0.01`.

## Required approval

> I approve the AU-NSW sampling and annotation protocol for immutable frame
> self-pin `37af88495c8896e83028b4692a10f18f2dd5a5e4dcad6b6140f40312f64d4000`
> and stored frame SHA-256
> `d09deb2ce966fb1b13ef33244f542a4c897df534baaeab94e7bc064c10643176`:
> census frame of 115 eligible units; exclude the 64 metadata-only records;
> deterministic 100-unit no-replacement paired annotation workload; seed
> `20260721`; exact-text SHA-256 singleton duplicate clusters; codebook
> the NSW-specific candidate codebook at
> `examples/v2/au-nsw-assertion-codebook.v0.2.0.pending.json` with its
> SHA-256 `3b8d76366e7dccb52e52a5e2275469ea4b52bc54eacff00b89c0bf26a8d6a49f`;
> two independent automated annotator roles and one distinct automated
> adjudicator role; and reliability thresholds raw agreement `>= 0.80`, kappa
> `>= 0.60`, exact-span agreement and overlap F1 at IoU `0.50`, with 10,000
> cluster-bootstrap replicates and seed `20260721`.
>
> This authorizes only deterministic membership creation and, after membership
> is approved, blinded packet generation and bounded annotation/adjudication
> under the stated roles. It does not authorize extractor metrics, gold
> promotion, publication, redistribution, training, legal certification,
> profile promotion, push, pull request, or merge.
