# AU RightToKnow CDX candidate validation

## Decision

Run `30236042144` is a complete, hash-verified Internet Archive CDX metadata
export for the approved RightToKnow URL scope. It is suitable as discovery and
capture-availability evidence. It is not an empirical source artifact and is
not eligible for empirical freezing.

The candidate immutable-manifest packet remains non-final.

## Integrity and coverage

- Workflow artifact: `alaveteli-all-captures-au-rtk-30236042144`
- Artifact ID: `8641731722`
- Artifact SHA-256:
  `1034e55f8bdfaddc1aa3ad1c1839aed9d0583641281ddd0dc88eb3a4db6c49b2`
- CDX SHA-256:
  `954b0f80ad2a44038f364d240cc9baac815f252a43535c8403dec060ddb730bd`
- Retrieval-evidence SHA-256:
  `0795be14775616416f61fb4131c397e7f2496f72c9fc534a357a98ec6e827331`
- Scope: `https://www.righttoknow.org.au/request/*`
- Retrieval time: `2026-07-27T04:03:29.802215Z`
- Pagination: complete, 26 contiguous pages
- Records: 26,000; all 26,000 conform to the approved host and path prefix
- Unique original URLs: 11,958
- Unique `(original, timestamp, digest)` capture keys: 25,632
- Duplicate rows under that key: 368

Duplicate rows are retained in the approved artifact. The counts above describe
the artifact and do not alter it.

## Metadata-only jurisdiction result

| Classification | Records |
|---|---:|
| AU-CTH | 0 |
| AU-NSW | 0 |
| Unresolved | 26,000 |

The CDX export contains only original URL, timestamp, digest, status code, and
length. None is an authority-identity field. Request slugs can contain names
but are not a governed crosswalk and cannot establish the applicable legal
regime. The metadata-only classifier therefore fails closed and leaves every
record unresolved.

Resolving AU-CTH versus AU-NSW requires a separately authorized source of
authority identity, such as archived-page replay or a hash-pinned external
authority/request crosswalk. Neither is authorized by the approval applied to
this packet.

## Rights and state boundary

The raw CDX artifact is not stored in this repository. Publication,
redistribution, replay, full-text retrieval, import, enrichment, manifest
finalization, empirical freezing, annotation, training, legal certification,
and profile promotion remain prohibited.
