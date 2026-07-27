# AU-CTH retained-HTML text-validation approval packet

## Proposed operation

Perform restricted-local source-text extraction and validation only on the
already retained canonical HTML snapshots within the finalized AU RightToKnow
replay population. This is a bounded readiness operation, not an empirical
frame freeze or annotation run.

## Exact scope

| Item | Value |
| --- | --- |
| Parent immutable manifest self-pin | `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c` |
| Parent stored-file SHA-256 | `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393` |
| Classification-summary SHA-256 | `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab` |
| AU-CTH classified records | 1,578 |
| AU-CTH retained canonical HTML snapshots | 517 |
| AU-CTH retained canonical JSON snapshots | 1,061 |
| Network access | None: use only the already retained 517 raw HTML files |

For each of the 517 HTML records, the operation would verify its raw hash,
extract only request-linked text available in the retained snapshot, record
UTF-8 character-offset spans and an explicit accessibility/rights disposition,
and produce a non-final candidate text-validation report. It must reject
navigation, attachment, response, or externally linked material; it may not
follow links, replay another capture, access the live origin, or expand the
population.

The 1,061 JSON-only AU-CTH records remain excluded from this operation because
their retained JSON has metadata and event IDs but no request/message text.
The result cannot be used to infer coverage for the 1,578-record AU-CTH
population, freeze an empirical frame, sample units, or annotate.

## Required decision

> I authorize restricted-local source-text extraction and validation from the
> existing 517 retained canonical HTML AU-CTH snapshots only, bounded by
> immutable manifest self-pin
> `2e64cac3f534265a68716ed0db7e9b82039200ee3a8312e6bb145a1af91bc23c`,
> stored-file SHA-256
> `c77ce6aafad557f5555fe347d2e9025d07e460574c15a4343728bb1ba3015393`, and
> classification-summary SHA-256
> `98eae70428e630cbd36849e5ad19c4133dbd9f01c413cf33221d2b0eef0091ab`.
> This authorizes only local hash verification, request-linked text/span
> extraction, rights/accessibility disposition, and a non-final candidate
> validation report. It does not authorize network access, archived-page
> replay, live-origin access, population expansion, empirical-frame freezing,
> sampling, annotation, adjudication, metrics, publication, redistribution,
> training, legal certification, profile promotion, push, pull request, or
> merge.

## Consequence of approval

An approval would establish whether the retained HTML subset contains
rights-eligible, span-validatable material. Any subsequent freeze would need a
new approval naming the resulting candidate report and its exact eligible
membership; no population-wide inference would be permitted.

## Recorded outcome

The authorized local operation completed on 2026-07-27. It validated all 517
retained AU-CTH canonical HTML members against the immutable manifest and
classification input, with no network access or replay. All 517 contained
extractable correspondence text and exact UTF-8 character spans. The
non-final summary is restricted-local at
`/Volumes/PortableSSD/foio-restricted/au-rtk-30236042144/retained-html-text-candidate/summary.json`,
SHA-256 `efd5e6be4e588eb3d1f0eaa15104595da41faaa0c89d5b1d3958afbb9f97b8e6`.
Its candidate JSONL has SHA-256
`a09c4b8fc2cf01ca957c3c0c8d3963ab0e0a37253a6fbcf6731cc889a9ed8c34`.

This does not establish empirical rights eligibility, freeze a frame, or
authorize sampling or annotation. Each candidate record remains marked
`restricted_local_non_redistributable` and ineligible for empirical use until
the next human decision.
